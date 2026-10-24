// Read the painted head turn with Apple's Vision framework.
//
// Four hand-rolled detectors were tried on this art — dark-mass centroid,
// eye pair, mouth blob, nose blob — and they disagreed with each other, so
// none of them is authoritative. Vision fits a face model to the image and
// returns *semantic* landmarks instead of guessing at dark blobs.
//
// The yaw angle itself is useless here: on painted art it collapses to
// -45/0/45 degrees. What survives is geometry, and geometry needs no label
// to be interpreted.
//
// Two features are measured, from different parts of the face:
//
//   1. the nose tip, taken as the last point of the nose crest
//   2. the centre of the mouth outline
//
// Each is reported as its offset from the midpoint of the two eyes, in units
// of the eye span. A positive offset means the feature sits on the image's
// right, so the face points to the image's right.
//
// The sign is fixed by construction, not by comparison with any hand-made
// label. Two things have to hold for that: the region called leftEye really
// does sit left of rightEye, and the landmarks land on the features they
// claim to. Both are checked — the first on every face, the second with
// scripts/facing_overlay.swift, which draws the fit back onto the picture.
//
// The eye-width cue is deliberately NOT used: on this art it contradicts the
// nose and the mouth on every face, because the painted eye shapes differ
// more than the turn does.
//
// Usage: swift scripts/facing_vision.swift <image.png> [...]
// Prints: <path>\t<nameCheck>\t<noseTipOffset>\t<mouthOffset>

import Foundation
import Vision
import CoreGraphics
import ImageIO

func points(_ region: VNFaceLandmarkRegion2D?) -> [CGPoint] {
    guard let r = region else { return [] }
    var out: [CGPoint] = []
    for i in 0..<r.pointCount {
        out.append(r.normalizedPoints[i])
    }
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
        return "ERR\tERR\tERR"
    }
    guard let face = request.results?.first, let marks = face.landmarks else {
        return "NONE\tNONE\tNONE"
    }

    let leftEye = points(marks.leftEye)
    let rightEye = points(marks.rightEye)
    let crest = points(marks.noseCrest)
    let lips = points(marks.outerLips)
    let leftCentre = centroid(leftEye)
    let rightCentre = centroid(rightEye)

    guard let leftCentre, let rightCentre, !leftEye.isEmpty, !rightEye.isEmpty,
          !crest.isEmpty, !lips.isEmpty else {
        return "NONE\tNONE\tNONE"
    }

    // The region named leftEye must sit to the left of the one named
    // rightEye, or the sign of everything below means nothing.
    let nameCheck = (leftCentre.x < rightCentre.x) ? "ok" : "SWAPPED"

    let midX = (leftCentre.x + rightCentre.x) / 2
    let span = abs(rightCentre.x - leftCentre.x)
    guard span > 0.01 else { return nameCheck + "\tNONE\tNONE" }

    let noseOffset = Double((crest.last!.x - midX) / span)
    let mouthCentre = centroid(lips)!
    let mouthOffset = Double((mouthCentre.x - midX) / span)

    return String(format: "%@\t%.4f\t%.4f", nameCheck, noseOffset, mouthOffset)
}

for path in CommandLine.arguments.dropFirst() {
    guard let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        print("\(path)\tERR\tERR\tERR")
        continue
    }
    print("\(path)\t\(analyze(image))")
}
