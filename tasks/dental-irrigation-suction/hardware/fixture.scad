// Millimetres. Printable inert training fixture; no clinical anatomy claim.
// OpenSCAD 2021.01+: openscad -o fixture.stl fixture.scad
// Stands: openscad -D 'part="stand"' -o stand.stl fixture.scad (print twice)
// Handle: openscad -D 'part="handle"' -o handle.stl fixture.scad (print twice)
// Global tabletop origin is local (x+270,y,z). Nominal print tolerance +/-0.5.
part="fixture";
$fn=64;
module box(s,p) {translate(p) cube(s,center=true);}
module crown(x,y) {
 translate([x,y,30]) cylinder(d=20,h=14,center=true);
 for(dx=[-4,4],dy=[-4,4])
  translate([x+dx,y+dy,37]) scale([4.5,4.5,3]) sphere(r=1);
}
module fixture() {
 difference() {
  union() {
   box([170,130,12],[0,0,6]);
   for(y=[-25,25]) box([115,28,18],[0,y,19]);
   box([28,70,18],[-61,0,19]);
   translate([5,0,18]) scale([43,10,7]) sphere(r=1);
   for(x=[-35,0,35],y=[-25,25]) crown(x,y);
   for(y=[-18,0,18]) box([12,12,18],[-61,y,35]);
   // Solid supports beneath a connected open channel; wetted floor is z=31.
   for(x=[-35,0,35]) box([30,20,22.5],[x,0,23.25]);
   for(x=[-17.5,17.5]) box([7,5,22.5],[x,0,23.25]);
  }
  // 28x18 cells and 7x3 channels; subtract above nominal floor.
  for(x=[-35,0,35]) box([28,18,20],[x,0,41]);
  for(x=[-17.5,17.5]) box([7.02,3,20],[x,0,41]);
 }
}
module handle() {
 // Bottom sits on rack; stock tube is secured externally with cable ties.
 // Top-loading ballast pocket; close flush with tape after weighing.
 difference() {
  union() {
   translate([-14,-12,0]) cube([28,24,55]);
   translate([-14.5,-12.5,31]) cube([29,25,20]);
  }
  translate([-8,-6,16]) cube([16,12,40]);
 }
}
if(part=="fixture") fixture();
else if(part=="stand") cylinder(d=50,h=30);
else if(part=="handle") handle();
else assert(false,"part must be fixture, stand or handle");
