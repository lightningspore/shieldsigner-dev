// ShieldSigner modular LCD enclosure. Units: mm.
// Assembly frame: carrier centre XY; carrier top Z=0; front is +Z.
// Prototype geometry: run the fit checker before treating exports as printable.
render_part = "base"; // base | bezel | button | retainer-left | retainer-right | camera-tray | camera-clamp | assembly
$fn = 96;
wall = 2.4;
outer_size = [176,82];
inner_size = [164,74];
floor_z = -23.4;
floor_inner_z = floor_z + wall;
seam_z = 0.4;
front_z = 21;
front_inner_z = front_z-wall;
carrier_bottom_z = -1.6;
mount_x = [-35.25,47.25];
mount_y = [-23.9,23.9];
closure_x = [-84.5,84.5];
camera_xy = [7,17];
camera_board = 26; // Assumed maximum; measure the purchased low-profile module.
camera_clear_opening = 22; // Captures centred 24..26 mm boards on their edges.
camera_front_z = -12.6;
camera_pcb_thickness = 1.2;
camera_screw_pitch = 29;
service_xy = [-34,22];
button_xy = [[-70.02,0],[-59.53,10.494],[-59.53,0],
             [-59.53,-10.426],[-49.08,0],[58.88,10.284],
             [58.88,0.014],[58.88,-10.316]];
retainer_mounts = [[-67.2,7.7],[-67.2,-7.7],[-51.8,7.7],
                   [66.5,7],[66.5,-7]];

module capsule(size,h,z=0) {
    translate([0,0,z]) linear_extrude(h)
        hull() for(x=[-(size[0]-size[1])/2,(size[0]-size[1])/2])
            translate([x,0]) circle(d=size[1]);
}
module bore(x,y,z,h,d) {translate([x,y,z]) cylinder(h=h,d=d);}
module outer_shell(z0,z1) {
    difference() {
        capsule(outer_size,z1-z0,z0);
        capsule(inner_size,z1-z0+0.02,z0-0.01);
    }
}
module base_assembled() {
    difference() {
        union() {
            capsule(outer_size,wall,floor_z);
            outer_shell(floor_inner_z,seam_z);
            for(x=mount_x,y=mount_y) {
                if(!(x==mount_x[0] && y==mount_y[1])) {
                // Narrow top respects the PCB's 5 mm mounting keepouts.
                translate([x,y,floor_inner_z]) cylinder(h=8,r1=5,r2=2.5);
                bore(x,y,floor_inner_z+7.9,carrier_bottom_z-floor_inner_z-7.9,5);
                }
            }
            for(x=closure_x) bore(x,0,floor_inner_z,seam_z-floor_inner_z,6);
            for(x=[-1,1],y=[-1,1])
                bore(camera_xy[0]+x*camera_screw_pitch/2,
                     camera_xy[1]+y*camera_screw_pitch/2,floor_inner_z,
                     camera_front_z-1.2-floor_inner_z,4.6);
            for(x=[-14,14],y=[-14,14])
                bore(service_xy[0]+x,service_xy[1]+y,floor_inner_z,4,4.6);
        }
        for(x=mount_x,y=mount_y) {
            if(!(x==mount_x[0] && y==mount_y[1])) {
            bore(x,y,floor_z-0.01,carrier_bottom_z-floor_z+0.02,2.8);
            translate([x,y,floor_z-0.01]) cylinder(h=1.2,d1=5.2,d2=2.8);
            }
        }
        for(x=closure_x) bore(x,0,seam_z-12,12.01,2.1);
        // Open-top access avoids unsupported roofs in the base print.
        translate([-39,-48,-8]) cube([15,16,9]); // Carrier USB-C
        translate([-18.5,-48,-7]) cube([60,15,8]); // ISO-card entrance
        translate([-43,16,-20]) cube([18,32,21]); // Luckfox USB / microSD
        translate([service_xy[0]-12,service_xy[1]-12,floor_z-0.01]) cube([24,24,wall+0.02]);
        for(x=[-14,14],y=[-14,14]) {
            bore(service_xy[0]+x,service_xy[1]+y,floor_z-0.01,5.51,1.6);
            translate([service_xy[0]+x,service_xy[1]+y,floor_z+5.49]) cylinder(h=0.81,d1=1.62,d2=0);
        }
        bore(camera_xy[0],camera_xy[1],floor_z-0.01,wall+0.02,22);
        for(x=[-1,1],y=[-1,1])
            bore(camera_xy[0]+x*camera_screw_pitch/2,
                 camera_xy[1]+y*camera_screw_pitch/2,floor_inner_z,
                 camera_front_z-1.2-floor_inner_z+0.01,1.6);
    }
}
module bezel_assembled() {
    difference() {
        union() {
            capsule(outer_size,wall,front_inner_z);
            outer_shell(seam_z,front_inner_z+0.01);
            // Join the locating lip to the shell above the PCB top face.
            difference() {
                capsule(outer_size,1.62,seam_z);
                hull() {
                    // Radius expands 1.62 mm over 1.62 mm Z. The cavity is
                    // 0.01 mm inside the lip bore at its top: positive overlap.
                    capsule([160.76,70.76],0.01,seam_z-0.01);
                    capsule(inner_size,0.02,seam_z+1.61);
                }
            }
            difference() {
                capsule([163.4,73.4],2.1,seam_z-2);
                capsule([161,71],2.12,seam_z-2.01);
                for(x=closure_x) bore(x,0,seam_z-2.01,2.12,6.8);
            }
            for(x=closure_x) bore(x,0,seam_z,front_inner_z-seam_z+0.01,6);
            for(p=retainer_mounts) bore(p[0],p[1],16.85,front_inner_z-16.85+0.01,5);
        }
        // Active area 57.6 x 43.2; 0.5 mm aperture allowance each edge.
        translate([6-58.6/2,-44.2/2,front_inner_z-0.01]) cube([58.6,44.2,wall+0.02]);
        for(p=button_xy) bore(p[0],p[1],front_inner_z-0.01,wall+0.02,7.4);
        for(p=retainer_mounts) bore(p[0],p[1],16.79,3.5,1.6);
        for(x=closure_x) {
            bore(x,0,seam_z-0.01,front_z-seam_z+0.02,2.8);
            translate([x,0,front_z-1.2]) cylinder(h=1.21,d1=2.8,d2=5.2);
        }
        // Continue the USB access into the locating lip and lower bezel wall.
        translate([-39,-48,-8]) cube([15,16,10]);
        translate([-18.5,-48,-7]) cube([60,15,7.1]);
    }
}
module button_assembled() {
    // 0.1 mm nominal switch gap; retainer limits downward travel to 0.35 mm.
    bore(0,0,2.6,1,2);
    translate([0,0,3.59]) cylinder(h=1.01,d1=2,d2=4);
    bore(0,0,4.59,12.62,4);
    translate([0,0,17.2]) cylinder(h=1.2,d1=9,d2=6.8);
    bore(0,0,18.39,3.61,6.8);
}
module retainer_assembled(left=true) {
    indices=left?[0,1,2,3,4]:[5,6,7];
    mounts=left?[0,1,2]:[3,4];
    difference() {
        hull() {
            for(i=indices) bore(button_xy[i][0],button_xy[i][1],15.2,1.65,11);
            for(i=mounts) bore(retainer_mounts[i][0],retainer_mounts[i][1],15.2,1.65,5);
        }
        for(i=indices) bore(button_xy[i][0],button_xy[i][1],15.19,1.67,4.6);
        for(i=mounts) bore(retainer_mounts[i][0],retainer_mounts[i][1],15.19,1.67,2.2);
    }
}
module camera_ring(clamp=false) {
    // Edge capture avoids assuming undocumented camera mounting-hole positions.
    z=clamp?camera_front_z+camera_pcb_thickness:camera_front_z-1.2;
    h=clamp?1.6:1.2;
    difference() {
        union() {
            translate([-17,-17,z]) cube([34,34,h]);
            if(!clamp) difference() {
                translate([-17,-17,z+h-0.01]) cube([34,34,camera_pcb_thickness+0.01]);
                translate([-(camera_board+0.6)/2,-(camera_board+0.6)/2,z+h-0.02])
                    cube([camera_board+0.6,camera_board+0.6,camera_pcb_thickness+0.04]);
            }
        }
        translate([-camera_clear_opening/2,-camera_clear_opening/2,z-0.01])
            cube([camera_clear_opening,camera_clear_opening,4]);
        for(x=[-1,1],y=[-1,1])
            bore(x*camera_screw_pitch/2,y*camera_screw_pitch/2,z-0.01,4,2.2);
        // Connector/ribbon exit: north wall remains open on both pieces.
        translate([-8,10,z-0.01]) cube([16,10,4]);
    }
}
module service_cover_assembled() {
    difference() {
        translate([service_xy[0]-17,service_xy[1]-17,floor_z-2]) cube([34,34,2]);
        for(x=[-14,14],y=[-14,14]) {
            bore(service_xy[0]+x,service_xy[1]+y,floor_z-2.01,2.02,2.2);
            translate([service_xy[0]+x,service_xy[1]+y,floor_z-2.01]) cylinder(h=1.01,d1=4.2,d2=2.2);
        }
    }
}
if(render_part=="base") translate([0,0,-floor_z]) base_assembled();
else if(render_part=="bezel") translate([0,0,front_z]) rotate([180,0,0]) bezel_assembled();
else if(render_part=="button") translate([0,0,22]) rotate([180,0,0]) button_assembled();
else if(render_part=="retainer-left") translate([59.53,0,-15.2]) retainer_assembled(true);
else if(render_part=="retainer-right") translate([-62,0,-15.2]) retainer_assembled(false);
else if(render_part=="camera-tray") translate([0,0,-camera_front_z+1.2]) camera_ring(false);
else if(render_part=="camera-clamp") translate([0,0,-camera_front_z-camera_pcb_thickness]) camera_ring(true);
else if(render_part=="service-cover") translate([-service_xy[0],-service_xy[1],-floor_z+2]) service_cover_assembled();
else if(render_part=="button-fit-coupon") difference() {
    translate([-21,-8,0]) cube([42,16,wall]);
    for(i=[0:2]) bore((i-1)*12,0,-0.01,wall+0.02,7.2+i*0.2);
}
else if(render_part=="assembly") {
    color("slategray") base_assembled();
    color("silver",0.65) bezel_assembled();
    color("orange") for(p=button_xy) translate([p[0],p[1],0]) button_assembled();
    color("teal") {retainer_assembled(true);retainer_assembled(false);}
    color("purple") translate([camera_xy[0],camera_xy[1],0]) {camera_ring(false);camera_ring(true);}
    color("slategray") service_cover_assembled();
}
else assert(false,"Unknown render_part");
