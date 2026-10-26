//! Sensor binding selection recovered from CamHwIsp20::getBindedSnsEntNmByVd.
//! Inventory construction and live media-link probing remain separate operations.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MediaStatus {
    Missing,
    OpenFailed,
    EntityUnavailable,
    NoLinks,
    FirstLinkFlags(u32),
}
#[derive(Clone, Copy, Debug)]
pub struct Sensor<'a> {
    pub name: &'a str,
    pub has_isp: bool,
    pub isp_paths: [&'a str; 2],
    pub cif_paths: Option<[&'a str; 4]>,
    pub media: MediaStatus,
}
/// Preserve the original inventory iteration order. A CIF descriptor takes
/// priority over ISP paths, and path matching is substring-based, not equality.
/// Embedded NUL bytes are outside this checked string API's domain.
pub fn bound_sensor<'a>(sensors: &[Sensor<'a>], video: Option<&str>) -> Option<&'a str> {
    let video = video?;
    for sensor in sensors {
        if sensor.name.contains("1608") || !sensor.has_isp {
            continue;
        }
        let matched = match sensor.cif_paths {
            Some(paths) => paths.iter().any(|p| p.contains(video)),
            None => sensor.isp_paths.iter().any(|p| p.contains(video)),
        };
        if !matched {
            continue;
        }
        if sensor.name.contains("FakeCamera") || sensor.name.contains("_s_") {
            return Some(sensor.name);
        }
        match sensor.media {
            MediaStatus::Missing | MediaStatus::EntityUnavailable | MediaStatus::NoLinks => {
                continue
            }
            MediaStatus::OpenFailed => return None,
            // The pinned binary compares the full first-link flags to 1.
            MediaStatus::FirstLinkFlags(1) => return Some(sensor.name),
            MediaStatus::FirstLinkFlags(_) => continue,
        }
    }
    None
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn cif_precedence_and_exact_link_flags() {
        let mut sensor = Sensor {
            name: "m00_b_sc3336",
            has_isp: true,
            isp_paths: ["/dev/video1", ""],
            cif_paths: Some(["/dev/video2", "", "", ""]),
            media: MediaStatus::FirstLinkFlags(1),
        };
        assert_eq!(bound_sensor(&[sensor], Some("/dev/video1")), None);
        assert_eq!(
            bound_sensor(&[sensor], Some("/dev/video2")),
            Some(sensor.name)
        );
        sensor.media = MediaStatus::FirstLinkFlags(3);
        assert_eq!(bound_sensor(&[sensor], Some("/dev/video2")), None);
    }
}
