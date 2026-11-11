// Measure the painted head turn of a chibi face that the landmark geometry
// cannot fit, using two independent cues:
//
//   1. the yaw angle Vision reports for the face (a 3D pose estimate);
//   2. the horizontal offset of the nose tip from the midpoint of the face
//      outline, in units of the outline width.
//
// The landmark path in scripts/facing_vision.swift reads the nose crest and
// the mouth, and it needs the eyes to fit a face at all. A small painted
// chibi head with a hat brim or a heavy fringe can fail that fit while
// still being perfectly readable to a person. These two cues do not depend
// on the eye landmarks, so they cover the cases the first path cannot.
//
// Usage: swift scripts/facing_yaw.swift <image.png> [...]
// Prints: <path>\t<yaw>\t<noseOffsetFromOutline>\t<faceWidth>
import Foundation
import Vision
import CoreGraphics
import ImageIO

func points(_ region: VNFaceLandmarkRegion2D?) -> [CGPoint] {
    guard let r = region else { return [] }
    var out: [CGPoint] = []
    for i in 0..<r.pointCount { out.append(r.normalizedPoints[i]) }
    return out
}

func centroid(_ pts: [CGPoint]) -> CGPoint? {
    guard !pts.isEmpty else { return nil }
    var x: CGFloat = 0, y: CGFloat = 0
    for p in pts { x += p.x; y += p.y }
    return CGPoint(x: x / CGFloat(pts.count), y: y / CGFloat(pts.count))
}

func analyze(_ cgImage: CGImage) -> String {
    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    let request = VNDetectFaceLandmarksRequest()
    request.revision = VNDetectFaceLandmarksRequestRevision3
    do {
        try handler.perform([request])
    } catch {
        return "ERR\tNONE\tNONE"
    }
    guard let face = request.results?.first else { return "NOFACE\tNONE\tNONE" }
    let yaw = Double(face.yaw?.doubleValue ?? 0)
    let lm = face.landmarks
    let outline = points(lm?.faceContour)
    let nose = points(lm?.noseCrest)
    guard !outline.isEmpty, !nose.isEmpty else {
        return String(format: "NOFIT\t%.4f\tNONE", yaw)
    }
    let xs = outline.map { $0.x }
    let minX = xs.min()!, maxX = xs.max()!
    let width = maxX - minX
    let midX = (minX + maxX) / 2
    // The nose crest is a path; its last point is the tip, the one nearest
    // the lower edge of the face.
    let tip = nose.max(by: { $0.y < $1.y })!
    let offset = width > 0.01 ? Double((tip.x - midX) / width) : 0
    return String(format: "OK\t%.4f\t%.4f\t%.4f", yaw, offset, width)
}

for path in CommandLine.arguments.dropFirst() {
    let url = URL(fileURLWithPath: path)
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil),
          let cg = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
        print("\(path)\tERR\tNONE\tNONE"); continue
    }
    print("\(path)\t\(analyze(cg))")
}
