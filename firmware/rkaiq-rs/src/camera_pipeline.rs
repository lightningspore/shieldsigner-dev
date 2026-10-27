// Live Linux pipeline configuration. Included inside camera-probe's Linux module.
mod pipeline_configuration {
    use super::*;
    use shieldsigner_rkaiq::{
        isp_pipeline::{self, Backend, Format as PadFormat, InputRoute, Selection},
        media::{Link, LinksQuery, Pad},
    };
    use std::io::Read;
    use std::os::unix::fs::{FileTypeExt, MetadataExt};
    const G_SUBFMT: u32 = 0xc0585604;
    const S_SUBFMT: u32 = 0xc0585605;
    const G_SELECTION: u32 = 0xc040563d;
    const S_SELECTION: u32 = 0xc040563e;
    const SET_LINK: u32 = 0xc0347c03;
    const CIF_MEMORY: u32 = 0x400456c1;
    const ISP_MEMORY: u32 = 0x40045725;
    struct Bridge {
        path: String,
        pads: Vec<u32>,
    }
    struct LinkChange {
        media: String,
        source: u32,
        source_pad: u16,
        sink: u32,
        sink_pad: u16,
        enabled: bool,
    }
    struct Plan {
        sensor: String,
        isp: String,
        route: InputRoute,
        tx: Vec<String>,
        rx: Vec<String>,
        bridges: Vec<Bridge>,
        links: Vec<LinkChange>,
    }
    fn keys(v: &Value, allowed: &[&str]) -> io::Result<()> {
        let map = v
            .as_object()
            .ok_or_else(|| error("Expected a JSON object"))?;
        for key in map.keys() {
            if !allowed.contains(&key.as_str()) {
                return Err(error(format!("Unknown pipeline field: {key}")));
            }
        }
        Ok(())
    }
    fn path(v: &Value) -> io::Result<String> {
        let s = v.as_str().ok_or_else(|| error("Expected a device path"))?;
        if !s.starts_with("/dev/") || s.contains('\0') || s.len() > 255 {
            return Err(error("Pipeline device paths must be bounded /dev paths"));
        }
        Ok(s.into())
    }
    fn number(v: &Value, max: u64) -> io::Result<u32> {
        let n = v
            .as_u64()
            .ok_or_else(|| error("Expected unsigned pipeline index"))?;
        if n > max {
            return Err(error("Pipeline index is out of range"));
        }
        Ok(n as u32)
    }
    fn array<'a>(v: &'a Value, key: &str, max: usize) -> io::Result<&'a [Value]> {
        match v.get(key) {
            None => Ok(&[]),
            Some(x) => {
                let a = x
                    .as_array()
                    .ok_or_else(|| error(format!("Expected array: {key}")))?;
                if a.len() > max {
                    return Err(error(format!("Too many entries: {key}")));
                }
                Ok(a)
            }
        }
    }
    fn parse(v: &Value) -> io::Result<Plan> {
        keys(
            v,
            &[
                "sensor", "isp", "route", "raw_tx", "raw_rx", "bridges", "links",
            ],
        )?;
        let sensor = path(&v["sensor"])?;
        let isp = path(&v["isp"])?;
        let route = match v["route"].as_str() {
            Some("direct-isp") => InputRoute::DirectIsp,
            Some("cif") => InputRoute::Cif,
            _ => return Err(error("route must be direct-isp or cif")),
        };
        // The first functional path is one linear camera: at most one TX/RX.
        let tx = array(v, "raw_tx", 1)?
            .iter()
            .map(path)
            .collect::<io::Result<Vec<_>>>()?;
        let rx = array(v, "raw_rx", 1)?
            .iter()
            .map(path)
            .collect::<io::Result<Vec<_>>>()?;
        let mut bridges = Vec::new();
        for b in array(v, "bridges", 8)? {
            keys(b, &["device", "pads"])?;
            let device = path(&b["device"])?;
            let pads = array(b, "pads", 4)?
                .iter()
                .map(|v| number(v, u32::MAX as u64))
                .collect::<io::Result<Vec<_>>>()?;
            if pads.is_empty() || pads.iter().enumerate().any(|(i, p)| pads[..i].contains(p)) {
                return Err(error("Bridge pads must be nonempty and unique"));
            }
            bridges.push(Bridge { path: device, pads });
        }
        let all: Vec<&str> = std::iter::once(sensor.as_str())
            .chain(std::iter::once(isp.as_str()))
            .chain(tx.iter().map(String::as_str))
            .chain(rx.iter().map(String::as_str))
            .chain(bridges.iter().map(|b| b.path.as_str()))
            .collect();
        if all.iter().enumerate().any(|(i, p)| all[..i].contains(p)) {
            return Err(error(
                "Pipeline sensor/ISP/raw/bridge device roles must be distinct",
            ));
        }
        let mut links = Vec::new();
        for l in array(v, "links", 64)? {
            keys(
                l,
                &[
                    "media",
                    "source",
                    "source_pad",
                    "sink",
                    "sink_pad",
                    "enabled",
                ],
            )?;
            let change = LinkChange {
                media: path(&l["media"])?,
                source: number(&l["source"], u32::MAX as u64)?,
                source_pad: number(&l["source_pad"], u16::MAX as u64)? as u16,
                sink: number(&l["sink"], u32::MAX as u64)?,
                sink_pad: number(&l["sink_pad"], u16::MAX as u64)? as u16,
                enabled: l["enabled"]
                    .as_bool()
                    .ok_or_else(|| error("Link enabled must be boolean"))?,
            };
            if change.source == 0
                || change.sink == 0
                || links.iter().any(|old: &LinkChange| {
                    old.media == change.media
                        && old.source == change.source
                        && old.source_pad == change.source_pad
                        && old.sink == change.sink
                        && old.sink_pad == change.sink_pad
                })
            {
                return Err(error("Link IDs must be nonzero and link requests unique"));
            }
            links.push(change);
        }
        Ok(Plan {
            sensor,
            isp,
            route,
            tx,
            rx,
            bridges,
            links,
        })
    }
    fn open_node(path: &str) -> io::Result<File> {
        let f = open(path, true)?;
        if !f.metadata()?.file_type().is_char_device() {
            return Err(error("Pipeline endpoints must be character devices"));
        }
        Ok(f)
    }
    fn call<T>(
        trace: &mut Vec<Value>,
        file: &File,
        path: &str,
        operation: &str,
        request: u32,
        record: &mut T,
        describe: impl Fn(&T) -> Value,
    ) -> io::Result<()> {
        let before = describe(record);
        let result = ioctl(file.as_raw_fd(), request, record);
        trace.push(json!({"device":path,"operation":operation,"request":format!("0x{request:08x}"),"input":before,"output":describe(record),"success":result.is_ok(),"errno":result.as_ref().err().and_then(io::Error::raw_os_error),"error":result.as_ref().err().map(|e|e.to_string())}));
        result
    }
    fn pad_view(f: &PadFormat) -> Value {
        json!({"which":get32(f,0),"pad":get32(f,4),"width":get32(f,8),"height":get32(f,12),"mediaBusCode":get32(f,16)})
    }
    fn selection_view(s: &Selection) -> Value {
        json!({"which":get32(s,0),"pad":get32(s,4),"target":get32(s,8),"left":get32(s,16) as i32,"top":get32(s,20) as i32,"width":get32(s,24),"height":get32(s,28)})
    }
    fn get_pad(trace: &mut Vec<Value>, file: &File, path: &str, pad: u32) -> io::Result<PadFormat> {
        let mut f = [0; 88];
        put32(&mut f, 0, 1);
        put32(&mut f, 4, pad);
        call(
            trace,
            file,
            path,
            "get-subdev-format",
            G_SUBFMT,
            &mut f,
            pad_view,
        )?;
        Ok(f)
    }
    fn valid_dimensions(width: u32, height: u32) -> io::Result<()> {
        if width == 0 || height == 0 || width > 65535 || height > 65535 {
            Err(error("Driver returned invalid pipeline dimensions"))
        } else {
            Ok(())
        }
    }
    fn find_link(trace: &mut Vec<Value>, file: &File, c: &LinkChange) -> io::Result<Link> {
        let mut entity = [0u8; 256];
        put32(&mut entity, 0, c.source);
        call(
            trace,
            file,
            &c.media,
            "get-link-source",
            0xc1007c01,
            &mut entity,
            |e| json!({"id":get32(e,0),"name":cstr(&e[4..36])}),
        )?;
        let pad_count = u16::from_ne_bytes(entity[52..54].try_into().unwrap()) as usize;
        let link_count = u16::from_ne_bytes(entity[54..56].try_into().unwrap()) as usize;
        if pad_count > 4096 || link_count > 4096 {
            return Err(error("Unreasonable media pad/link count"));
        }
        let mut pads = vec![Pad::default(); pad_count];
        let mut links = vec![Link::default(); link_count];
        let mut query = LinksQuery {
            entity: c.source,
            pads: if pads.is_empty() {
                ptr::null_mut()
            } else {
                pads.as_mut_ptr()
            },
            links: if links.is_empty() {
                ptr::null_mut()
            } else {
                links.as_mut_ptr()
            },
            reserved: [0; 4],
        };
        let request = (3u32 << 30)
            | ((std::mem::size_of::<LinksQuery>() as u32) << 16)
            | ((b'|' as u32) << 8)
            | 2;
        call(
            trace,
            file,
            &c.media,
            "enumerate-source-links",
            request,
            &mut query,
            |_| json!({"entity":c.source,"padCount":pad_count,"linkCount":link_count}),
        )?;
        let link = links
            .into_iter()
            .find(|l| {
                l.source.entity == c.source
                    && l.source.index == c.source_pad
                    && l.sink.entity == c.sink
                    && l.sink.index == c.sink_pad
            })
            .ok_or_else(|| error("Requested media link is not present in the current graph"))?;
        if link.flags & 0xf0000000 != 0 {
            return Err(error("Only media data links are supported"));
        }
        if link.flags & 2 != 0 && (link.flags & 1 != 0) != c.enabled {
            return Err(error(
                "Requested change conflicts with an immutable media link",
            ));
        }
        Ok(link)
    }
    struct PreparedLink<'a> {
        change: &'a LinkChange,
        file: File,
        link: Link,
    }
    struct RawNode {
        path: String,
        file: File,
        kind: u32,
    }
    impl RawNode {
        fn preflight(path: &str, output: bool, trace: &mut Vec<Value>) -> io::Result<Self> {
            let file = open_node(path)?;
            let mut cap = [0u8; 104];
            call(
                trace,
                &file,
                path,
                "raw-query-capabilities",
                0x80685600,
                &mut cap,
                |c| json!({"driver":cstr(&c[..16]),"card":cstr(&c[16..48]),"capabilities":get32(c,84),"deviceCapabilities":get32(c,88)}),
            )?;
            let caps = if get32(&cap, 84) & 0x80000000 != 0 {
                get32(&cap, 88)
            } else {
                get32(&cap, 84)
            };
            let kind = if output {
                if caps & 0x2000 != 0 {
                    10
                } else if caps & 2 != 0 {
                    2
                } else {
                    return Err(error("Raw RX node does not support video output"));
                }
            } else if caps & 0x1000 != 0 {
                9
            } else if caps & 1 != 0 {
                1
            } else {
                return Err(error("Raw TX node does not support video capture"));
            };
            if caps & 0x04000000 == 0 {
                return Err(error("Raw node does not support streaming"));
            }
            let mut format: Format = zero();
            format.kind = kind;
            call(
                trace,
                &file,
                path,
                "raw-get-format",
                GETFMT,
                &mut format,
                format_json,
            )?;
            Ok(Self {
                path: path.into(),
                file,
                kind,
            })
        }
        fn set(
            &self,
            width: u32,
            height: u32,
            pixel: u32,
            trace: &mut Vec<Value>,
        ) -> io::Result<()> {
            let mut format: Format = zero();
            format.kind = self.kind;
            unsafe {
                put32(&mut format.data.raw, 0, width);
                put32(&mut format.data.raw, 4, height);
                put32(&mut format.data.raw, 8, pixel);
                put32(&mut format.data.raw, 12, 1);
            }
            call(
                trace,
                &self.file,
                &self.path,
                "raw-set-format",
                SETFMT,
                &mut format,
                format_json,
            )?;
            let returned = unsafe { format.data.raw };
            if get32(&returned, 0) != width
                || get32(&returned, 4) != height
                || get32(&returned, 8) != pixel
            {
                return Err(error(
                    "Raw driver changed requested dimensions/pixel format",
                ));
            }
            let mut readback: Format = zero();
            readback.kind = self.kind;
            call(
                trace,
                &self.file,
                &self.path,
                "raw-readback-format",
                GETFMT,
                &mut readback,
                format_json,
            )?;
            let returned = unsafe { readback.data.raw };
            if get32(&returned, 0) != width
                || get32(&returned, 4) != height
                || get32(&returned, 8) != pixel
            {
                return Err(error(
                    "Raw format readback does not match the configured pipeline",
                ));
            }
            Ok(())
        }
    }
    struct DevicePipeline<'a> {
        isp_path: &'a str,
        isp: File,
        tx: Vec<RawNode>,
        rx: Vec<RawNode>,
        trace: &'a mut Vec<Value>,
        raw_errors: Vec<String>,
    }
    impl Backend for DevicePipeline<'_> {
        fn set_tx_format(&mut self, f: &PadFormat, p: u32) {
            for node in &self.tx {
                if let Err(e) = node.set(get32(f, 8), get32(f, 12), p, self.trace) {
                    self.raw_errors.push(format!("{}: {e}", node.path));
                }
            }
        }
        fn set_rx_format(&mut self, f: &PadFormat, p: u32) {
            for node in &self.rx {
                if let Err(e) = node.set(get32(f, 8), get32(f, 12), p, self.trace) {
                    self.raw_errors.push(format!("{}: {e}", node.path));
                }
            }
        }
        fn bits_per_pixel(&mut self, _: u32) -> i8 {
            10
        }
        fn set_scaler_format(&mut self, _: &Selection, _: u32, _: i8) {
            self.raw_errors
                .push("Optional CIF scaler is not enabled in the linear startup adapter".into());
        }
        fn get_format(&mut self, which: u32, pad: u32, out: &mut PadFormat) -> i32 {
            out.fill(0);
            put32(out, 0, which);
            put32(out, 4, pad);
            match call(
                self.trace,
                &self.isp,
                self.isp_path,
                "isp-get-format",
                G_SUBFMT,
                out,
                pad_view,
            ) {
                Ok(()) => 0,
                Err(e) => -e.raw_os_error().unwrap_or(libc::EIO),
            }
        }
        fn set_format(&mut self, f: &mut PadFormat) -> i32 {
            match call(
                self.trace,
                &self.isp,
                self.isp_path,
                "isp-set-format",
                S_SUBFMT,
                f,
                pad_view,
            ) {
                Ok(()) => 0,
                Err(e) => -e.raw_os_error().unwrap_or(libc::EIO),
            }
        }
        fn set_selection(&mut self, s: &mut Selection) -> i32 {
            match call(
                self.trace,
                &self.isp,
                self.isp_path,
                "isp-set-crop",
                S_SELECTION,
                s,
                selection_view,
            ) {
                Ok(()) => 0,
                Err(e) => -e.raw_os_error().unwrap_or(libc::EIO),
            }
        }
    }
    fn execute(plan: &Plan, dry: bool, trace: &mut Vec<Value>) -> io::Result<Value> {
        let sensor = open_node(&plan.sensor)?;
        let isp = open_node(&plan.isp)?;
        let sensor_format = get_pad(trace, &sensor, &plan.sensor, 0)?;
        let width = get32(&sensor_format, 8);
        let height = get32(&sensor_format, 12);
        let bus = get32(&sensor_format, 16);
        valid_dimensions(width, height)?;
        if ![0x3007, 0x300a, 0x300e, 0x300f].contains(&bus) {
            return Err(error(
                "Initial linear adapter requires a supported RAW10 Bayer sensor format",
            ));
        }
        let pixel = shieldsigner_rkaiq::sensor_descriptor::pixel_format(bus);
        let mut crop = [0u8; 64];
        put32(&mut crop, 0, 1);
        put32(&mut crop, 8, 2);
        if call(
            trace,
            &sensor,
            &plan.sensor,
            "sensor-crop-bounds",
            G_SELECTION,
            &mut crop,
            selection_view,
        )
        .is_err()
        {
            crop.fill(0);
            put32(&mut crop, 0, 1);
            put32(&mut crop, 24, width);
            put32(&mut crop, 28, height);
            trace.push(json!({"operation":"sensor-crop-fallback","width":width,"height":height,"usesFullSensorFormat":true}));
        }
        valid_dimensions(get32(&crop, 24), get32(&crop, 28))?;
        get_pad(trace, &isp, &plan.isp, 0)?;
        get_pad(trace, &isp, &plan.isp, 2)?;
        let tx = plan
            .tx
            .iter()
            .map(|p| RawNode::preflight(p, false, trace))
            .collect::<io::Result<Vec<_>>>()?;
        let rx = plan
            .rx
            .iter()
            .map(|p| RawNode::preflight(p, true, trace))
            .collect::<io::Result<Vec<_>>>()?;
        let mut bridges = Vec::new();
        for bridge in &plan.bridges {
            let file = open_node(&bridge.path)?;
            for pad in &bridge.pads {
                get_pad(trace, &file, &bridge.path, *pad)?;
            }
            bridges.push((bridge, file));
        }
        let mut roles = vec![
            (plan.sensor.as_str(), sensor.metadata()?.rdev()),
            (plan.isp.as_str(), isp.metadata()?.rdev()),
        ];
        for node in tx.iter().chain(rx.iter()) {
            roles.push((node.path.as_str(), node.file.metadata()?.rdev()));
        }
        for (bridge, file) in &bridges {
            roles.push((bridge.path.as_str(), file.metadata()?.rdev()));
        }
        for (i, (path, id)) in roles.iter().enumerate() {
            if let Some((other, _)) = roles[..i].iter().find(|(_, previous)| previous == id) {
                return Err(error(format!(
                    "Device roles alias the same character device: {other}, {path}"
                )));
            }
        }
        let mut links = Vec::new();
        for change in &plan.links {
            let file = open_node(&change.media)?;
            let link = find_link(trace, &file, change)?;
            links.push(PreparedLink { change, file, link });
        }
        let mut summary = json!({"route":if plan.route==InputRoute::Cif{"cif"}else{"direct-isp"},"sensor":pad_view(&sensor_format),"crop":selection_view(&crop),"rawPixelFormat":fourcc(pixel),"rawTxCount":tx.len(),"rawRxCount":rx.len(),"plannedLinkCount":links.len(),"plannedBridgeCount":bridges.len()});
        if dry {
            return Ok(summary);
        }
        // Every endpoint/link was queried before the first mutation.
        for prepared in &mut links {
            let desired = if prepared.change.enabled {
                prepared.link.flags | 1
            } else {
                prepared.link.flags & !1
            };
            if desired != prepared.link.flags {
                prepared.link.flags = desired;
                call(
                    trace,
                    &prepared.file,
                    &prepared.change.media,
                    "set-media-link",
                    SET_LINK,
                    &mut prepared.link,
                    |l| json!({"source":l.source.entity,"sourcePad":l.source.index,"sink":l.sink.entity,"sinkPad":l.sink.index,"flags":l.flags}),
                )?;
            }
            let actual = find_link(trace, &prepared.file, prepared.change)?;
            if (actual.flags & 1 != 0) != prepared.change.enabled {
                return Err(error("Media link readback differs from requested state"));
            }
        }
        for (bridge, file) in &bridges {
            for pad in &bridge.pads {
                let mut f = get_pad(trace, file, &bridge.path, *pad)?;
                f[8..20].copy_from_slice(&sensor_format[8..20]);
                call(
                    trace,
                    file,
                    &bridge.path,
                    "set-bridge-format",
                    S_SUBFMT,
                    &mut f,
                    pad_view,
                )?;
                if f[8..20] != sensor_format[8..20] {
                    return Err(error(
                        "Bridge adjusted the sensor dimensions/media bus code",
                    ));
                }
            }
        }
        let mut adapter = DevicePipeline {
            isp_path: &plan.isp,
            isp,
            tx,
            rx,
            trace,
            raw_errors: Vec::new(),
        };
        let status = if plan.route == InputRoute::DirectIsp {
            isp_pipeline::setup(
                &mut adapter,
                isp_pipeline::Configuration {
                    shared_cif: false,
                    shared_capture_first: true,
                    scaler: false,
                    pixel_format: pixel,
                },
                &sensor_format,
                &crop,
            )
        } else {
            let mut raw_format = sensor_format;
            raw_format[8..16].copy_from_slice(&crop[24..32]);
            if isp_pipeline::needs_word_alignment(get32(&crop, 24), 10) {
                for (nodes, request) in [(&adapter.tx, CIF_MEMORY), (&adapter.rx, ISP_MEMORY)] {
                    for node in nodes {
                        let mut mode = 2i32;
                        call(
                            adapter.trace,
                            &node.file,
                            &node.path,
                            "set-csi-high-alignment",
                            request,
                            &mut mode,
                            |m| json!({"mode":m}),
                        )?;
                    }
                }
            }
            adapter.set_tx_format(&raw_format, pixel);
            adapter.set_rx_format(&raw_format, pixel);
            isp_pipeline::configure_pads(&mut adapter, &sensor_format, &crop, InputRoute::Cif)
        };
        if status != 0 {
            return Err(error(format!(
                "ISP pad configuration failed with status {status}"
            )));
        }
        if !adapter.raw_errors.is_empty() {
            return Err(error(format!(
                "Raw format configuration failed: {:?}",
                adapter.raw_errors
            )));
        }
        summary["ispSinkReadback"] = pad_view(&get_pad(adapter.trace, &adapter.isp, &plan.isp, 0)?);
        summary["ispSourceReadback"] =
            pad_view(&get_pad(adapter.trace, &adapter.isp, &plan.isp, 2)?);
        Ok(summary)
    }
    pub(super) fn linear_cif_nodes(value: &Value) -> io::Result<(String, String, String, String)> {
        let plan = parse(value)?;
        if plan.route != InputRoute::Cif || plan.tx.len() != 1 || plan.rx.len() != 1 {
            return Err(error(
                "First-frame startup requires one explicit CIF raw TX/RX pair",
            ));
        }
        Ok((
            plan.sensor,
            plan.isp,
            plan.tx[0].clone(),
            plan.rx[0].clone(),
        ))
    }
    pub fn run(args: &[String]) -> io::Result<()> {
        if args.is_empty() || args.len() > 2 || (args.len() == 2 && args[1] != "--dry-run") {
            return Err(error("configure-pipeline requires PLAN.json [--dry-run]"));
        }
        if std::mem::size_of::<usize>() != 4 {
            return Err(error(
                "Pipeline configuration currently targets ARM32 Linux only",
            ));
        }
        let mut input = Vec::new();
        File::open(&args[0])?.take(65537).read_to_end(&mut input)?;
        if input.len() > 65536 {
            return Err(error("Pipeline plan exceeds 64 KiB"));
        }
        let value: Value = serde_json::from_slice(&input)
            .map_err(|e| error(format!("Invalid pipeline JSON: {e}")))?;
        let plan = parse(&value)?;
        let active = vendor_processes();
        if !active.is_empty() {
            return Err(error(format!(
                "Vendor camera processes still running: {active:?}"
            )));
        }
        let dry = args.len() == 2;
        let mut trace = Vec::new();
        let result = execute(&plan, dry, &mut trace);
        println!(
            "{}",
            serde_json::to_string_pretty(
                &json!({"tool":format!("camera-probe {}",env!("CARGO_PKG_VERSION")),"kind":"linear-raw10-pipeline-configuration","success":result.is_ok(),"dryRun":dry,"writesRequested":!dry,"error":result.as_ref().err().map(|e|e.to_string()),"configuration":result.as_ref().ok(),"operations":trace,"linksRkaiq":false,"startsStreaming":false,"initialParametersProvided":false,"coldStartProven":false,"limitations":["Explicit current-graph links/device roles; no guessed entity IDs, HDR, shared-camera ownership or optional CIF scaler.","Configuration does not allocate/start capture/parameter queues or generate calibrated initial ISP parameters.","Earlier accepted link/format changes remain on later failure; no automatic rollback.","Positive device operation and independent startup still require camera hardware."]})
            )?
        );
        result.map(|_| ())
    }
}
