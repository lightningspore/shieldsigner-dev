//! Linux media-controller ABI and bounded enabled-data-link traversal.
//! This topology analysis supplements the recovered vendor inventory selector;
//! it does not claim to reproduce the library's complete inventory constructor.
pub const CAMERA_SENSOR: u32 = 0x00020001;
#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct Pad {
    pub entity: u32,
    pub index: u16,
    pub flags: u32,
    pub reserved: [u32; 2],
}
#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct Link {
    pub source: Pad,
    pub sink: Pad,
    pub flags: u32,
    pub reserved: [u32; 2],
}
#[repr(C)]
pub struct LinksQuery {
    pub entity: u32,
    pub pads: *mut Pad,
    pub links: *mut Link,
    pub reserved: [u32; 4],
}
const _: () = assert!(core::mem::size_of::<Pad>() == 20);
const _: () = assert!(core::mem::size_of::<Link>() == 52);
#[cfg(target_pointer_width = "32")]
const _: () = assert!(core::mem::size_of::<LinksQuery>() == 28);
#[derive(Clone, Copy, Debug)]
pub struct Entity {
    pub id: u32,
    pub kind: u32,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Binding {
    None,
    Unique(u32),
    Ambiguous,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum GraphError {
    ScratchTooSmall,
    DuplicateEntity,
    MissingTarget,
    DanglingLink,
}
/// Walk enabled data links backwards from an image endpoint. Cycles terminate;
/// multiple upstream sensor entities are reported explicitly, never guessed.
/// The caller must supply a complete snapshot of this one media device.
pub fn upstream_sensor(
    entities: &[Entity],
    links: &[Link],
    target: u32,
    scratch: &mut [u32],
) -> Result<Binding, GraphError> {
    if scratch.len() < entities.len() {
        return Err(GraphError::ScratchTooSmall);
    }
    if !entities.iter().any(|e| e.id == target) {
        return Err(GraphError::MissingTarget);
    }
    for (i, e) in entities.iter().enumerate() {
        if entities[..i].iter().any(|other| other.id == e.id) {
            return Err(GraphError::DuplicateEntity);
        }
    }
    for link in links {
        if !entities.iter().any(|e| e.id == link.source.entity)
            || !entities.iter().any(|e| e.id == link.sink.entity)
        {
            return Err(GraphError::DanglingLink);
        }
    }
    scratch[0] = target;
    let mut head = 0;
    let mut len = 1;
    let mut binding = Binding::None;
    while head < len {
        let id = scratch[head];
        head += 1;
        if entities
            .iter()
            .any(|e| e.id == id && e.kind == CAMERA_SENSOR)
        {
            binding = match binding {
                Binding::None => Binding::Unique(id),
                Binding::Unique(previous) if previous == id => binding,
                _ => Binding::Ambiguous,
            };
        }
        for link in links {
            if link.sink.entity == id
                && link.flags & 1 != 0
                && link.flags & 0xf0000000 == 0
                && !scratch[..len].contains(&link.source.entity)
            {
                scratch[len] = link.source.entity;
                len += 1;
            }
        }
    }
    Ok(binding)
}
#[cfg(test)]
mod tests {
    use super::*;
    fn link(source: u32, sink: u32, flags: u32) -> Link {
        Link {
            source: Pad {
                entity: source,
                ..Pad::default()
            },
            sink: Pad {
                entity: sink,
                ..Pad::default()
            },
            flags,
            ..Link::default()
        }
    }
    #[test]
    fn follows_enabled_immutable_links_and_terminates_cycles() {
        let entities = [
            Entity {
                id: 1,
                kind: CAMERA_SENSOR,
            },
            Entity { id: 2, kind: 0 },
            Entity { id: 3, kind: 0 },
        ];
        let links = [link(1, 2, 3), link(2, 3, 1), link(3, 2, 1)];
        assert_eq!(
            upstream_sensor(&entities, &links, 3, &mut [0; 3]),
            Ok(Binding::Unique(1))
        );
        assert_eq!(
            upstream_sensor(&entities, &[link(1, 2, 0), link(2, 3, 1)], 3, &mut [0; 3]),
            Ok(Binding::None)
        );
    }
    #[test]
    fn rejects_ambiguity_and_incomplete_snapshots() {
        let entities = [
            Entity {
                id: 1,
                kind: CAMERA_SENSOR,
            },
            Entity {
                id: 2,
                kind: CAMERA_SENSOR,
            },
            Entity { id: 3, kind: 0 },
        ];
        assert_eq!(
            upstream_sensor(&entities, &[link(1, 3, 1), link(2, 3, 1)], 3, &mut [0; 3]),
            Ok(Binding::Ambiguous)
        );
        assert_eq!(
            upstream_sensor(&entities, &[link(9, 3, 1)], 3, &mut [0; 3]),
            Err(GraphError::DanglingLink)
        );
        assert_eq!(
            upstream_sensor(&entities, &[], 3, &mut [0; 2]),
            Err(GraphError::ScratchTooSmall)
        );
        assert_eq!(
            upstream_sensor(&entities, &[link(1, 3, 0x10000001)], 3, &mut [0; 3]),
            Ok(Binding::None)
        );
    }
}
