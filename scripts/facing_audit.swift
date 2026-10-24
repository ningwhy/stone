// Draw the Vision face fit back onto a picture so the reading can be audited by eye.
// Usage: swift scripts/facing_audit.swift <image> <out>
import AppKit
import Vision

let args = CommandLine.arguments
guard args.count == 3 else { print("usage: facing_audit <image> <out>"); exit(2) }
let url = URL(fileURLWithPath: args[1])
guard let image = NSImage(contentsOf: url), let tiff = image.tiffRepresentation,
      let rep = NSBitmapImageRep(data: tiff), let cg = rep.cgImage else {
    print("cannot read image"); exit(1)
}
let W = CGFloat(cg.width), H = CGFloat(cg.height)

let request = VNDetectFaceLandmarksRequest()
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try handler.perform([request])
guard let face = request.results?.first else { print("no face"); exit(1) }
let marks = face.landmarks!

func pts(_ region: VNFaceLandmarkRegion2D?) -> [CGPoint] {
    guard let region else { return [] }
    let points = region.normalizedPoints
    return (0..<points.count).map { points[$0] }
}
func px(_ p: CGPoint) -> CGPoint { CGPoint(x: p.x * W, y: (1 - p.y) * H) }
func centroid(_ points: [CGPoint]) -> CGPoint? {
    guard !points.isEmpty else { return nil }
    return CGPoint(x: points.map { $0.x }.reduce(0, +) / CGFloat(points.count),
                   y: points.map { $0.y }.reduce(0, +) / CGFloat(points.count))
}

let left = pts(marks.leftEye), right = pts(marks.rightEye), nose = pts(marks.nose), crest = pts(marks.noseCrest), lips = pts(marks.outerLips)
let lc = centroid(left)!, rc = centroid(right)!
let nameCheck = lc.x < rc.x ? "ok" : "SWAPPED"
let midX = (lc.x + rc.x) / 2
let span = abs(rc.x - lc.x)
let tip = crest.last ?? nose.last!
let noseOffset = Double((tip.x - midX) / span)
let mouthOffset = Double((centroid(lips)!.x - midX) / span)

let output = NSImage(size: NSSize(width: cg.width, height: cg.height))
output.lockFocus()
let ctx = NSGraphicsContext.current!.cgContext
ctx.draw(cg, in: NSRect(x: 0, y: 0, width: W, height: H))
func stroke(_ points: [CGPoint], _ color: NSColor, _ width: CGFloat) {
    ctx.setStrokeColor(color.cgColor); ctx.setLineWidth(width)
    for i in 0..<max(points.count - 1, 0) {
        let a = px(points[i]), b = px(points[i + 1])
        ctx.move(to: NSPoint(x: a.x, y: H - a.y)); ctx.addLine(to: NSPoint(x: b.x, y: H - b.y))
    }
    ctx.strokePath()
}
stroke(left, .systemBlue, 2); stroke(right, .systemBlue, 2)
stroke(nose, .systemGreen, 2); stroke(crest, .systemGreen, 2); stroke(lips, .systemOrange, 2)
stroke(pts(marks.faceContour), .systemPurple, 1.5)
let m = px(CGPoint(x: midX, y: lc.y))
ctx.setStrokeColor(NSColor.systemBlue.cgColor); ctx.setLineWidth(1.5)
ctx.move(to: NSPoint(x: m.x, y: 0)); ctx.addLine(to: NSPoint(x: m.x, y: H)); ctx.strokePath()
let t = px(tip)
ctx.setStrokeColor(NSColor.systemRed.cgColor); ctx.setLineWidth(3)
ctx.move(to: NSPoint(x: t.x - 8, y: H - t.y - 8)); ctx.addLine(to: NSPoint(x: t.x + 8, y: H - t.y + 8)); ctx.strokePath()
ctx.move(to: NSPoint(x: t.x + 8, y: H - t.y - 8)); ctx.addLine(to: NSPoint(x: t.x - 8, y: H - t.y + 8)); ctx.strokePath()
output.unlockFocus()
guard let out = output.tiffRepresentation, let outRep = NSBitmapImageRep(data: out),
      let data = outRep.representation(using: .png, properties: [:]) else { print("draw failed"); exit(1) }
try data.write(to: URL(fileURLWithPath: args[2]))
print("\(args[1])\t\(nameCheck)\t\(noseOffset)\t\(mouthOffset)")
