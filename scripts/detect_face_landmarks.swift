// Report the face landmarks of a painted character in **source pixels**.
//
// `scripts/detect_face_boxes.swift` finds where the face is; this finds the
// features inside it — the eye centres, the nose tip and the mouth centre.
// Two uses:
//
//   * the eye pair and the mouth bracket the face vertically, so their
//     positions say where the forehead and the chin are;
//   * the nose tip's offset from the eye midpoint is the same measurement
//     `scripts/facing_vision.swift` uses to decide which way the head turns.
//
// The landmarks come back in Vision's normalised, bottom-left-origin space,
// so the vertical axis is flipped back into image order before printing.
//
// Usage: swift scripts/detect_face_landmarks.swift <image.png> [...]
// Prints: <path>\t<x0,y0,x1,y1>\t<leftEyeX,leftEyeY>\t<rightEyeX,rightEyeY>\t<noseX,noseY>\t<mouthX,mouthY>

import Foundation
import Vision
import CoreGraphics
import ImageIO

func loadImage(_ path: String) -> CGImage? {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil) else {
        return nil
    }
    return CGImageSourceCreateImageAtIndex(src, 0, nil)
}

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

/// Vision's normalised landmark point -> source pixels (top-left origin).
///
/// The landmark points are normalised against the **face observation's own
/// bounding box** in a bottom-left-origin space, so both the box's origin and
/// its size have to be applied — scaling by the image size alone lands the
/// landmarks outside the face.
func toPixels(_ p: CGPoint, box: CGRect, width: CGFloat, height: CGFloat) -> (x: Double, y: Double) {
    let x = Double((box.origin.x + p.x * box.width) * width)
    let boxTop = height - (box.origin.y + box.height) * height
    let y = Double(boxTop + (1 - p.y) * box.height * height)
    return (x, y)
}

func fmt(_ v: (x: Double, y: Double)) -> String {
    String(format: "%.1f,%.1f", v.x, v.y)
}

for path in CommandLine.arguments.dropFirst() {
    guard let image = loadImage(path) else {
        print("\(path)\tERR\tERR\tERR\tERR\tERR")
        continue
    }
    let w = CGFloat(image.width)
    let h = CGFloat(image.height)
    let request = VNDetectFaceLandmarksRequest()
    request.revision = VNDetectFaceLandmarksRequestRevision3
    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    do {
        try handler.perform([request])
    } catch {
        print("\(path)\tERR\tERR\tERR\tERR\tERR")
        continue
    }
    guard let face = request.results?.first, let marks = face.landmarks else {
        print("\(path)\tNOFACE\t-\t-\t-\t-")
        continue
    }
    let leftEye = points(marks.leftEye)
    let rightEye = points(marks.rightEye)
    let crest = points(marks.noseCrest)
    let lips = points(marks.outerLips)
    guard let leftCentre = centroid(leftEye), let rightCentre = centroid(rightEye),
          let mouthCentre = centroid(lips), !crest.isEmpty else {
        print("\(path)\tPARTIAL\t-\t-\t-\t-")
        continue
    }
    // The nose tip is the last point of the nose crest.
    let nose = crest[crest.count - 1]
    let box = face.boundingBox
    let bx0 = box.origin.x * w
    let by0 = h - (box.origin.y + box.height) * h
    let bx1 = (box.origin.x + box.width) * w
    let by1 = h - box.origin.y * h
    print("\(path)\t\(Int(bx0)),\(Int(by0)),\(Int(bx1)),\(Int(by1))\t"
          + fmt(toPixels(leftCentre, box: box, width: w, height: h)) + "\t"
          + fmt(toPixels(rightCentre, box: box, width: w, height: h)) + "\t"
          + fmt(toPixels(nose, box: box, width: w, height: h)) + "\t"
          + fmt(toPixels(mouthCentre, box: box, width: w, height: h)))
}
