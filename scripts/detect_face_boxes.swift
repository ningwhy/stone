// Detect the face region of a painted character with Apple's Vision framework.
//
// The project's skin-tone detector (`scripts/inspect_face_boxes.py`) proposes
// boxes, but it latches onto hair, collars and scarves often enough that the
// proposal has to be checked by eye. Vision's own face detector finds the face
// *as a face*, so it is a second opinion on the same question: where does the
// painted head sit in this bitmap.
//
// The box is reported in **source pixels** of the image that was passed in,
// and it is expanded slightly: Vision's rectangle hugs the facial features
// tightly, while the project's face boxes are meant to cover the whole face
// from the hairline to the chin and to include the ears.
//
// Usage: swift scripts/detect_face_boxes.swift <image.png> [...]
// Prints: <path>\t<x0,y0,x1,y1>\t<confidence>

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

/// Vision's face rectangle, in source pixels, grown by a margin.
func detectFace(_ image: CGImage, margin: CGFloat) -> CGRect? {
    let request = VNDetectFaceRectanglesRequest()
    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    do {
        try handler.perform([request])
    } catch {
        return nil
    }
    guard let observation = request.results?.first else { return nil }

    // Vision works in normalised, bottom-left-origin coordinates.
    let box = observation.boundingBox
    let w = CGFloat(image.width)
    let h = CGFloat(image.height)
    var x0 = box.origin.x * w
    var y0 = box.origin.y * h
    var x1 = (box.origin.x + box.width) * w
    var y1 = (box.origin.y + box.height) * h
    // Flip the vertical axis back into image order (top-left origin).
    let top = h - y1
    let bottom = h - y0
    x0 = max(0, x0 - margin)
    x1 = min(w, x1 + margin)
    y0 = max(0, top - margin)
    y1 = min(h, bottom + margin)
    return CGRect(x: x0, y: y0, width: x1 - x0, height: y1 - y0)
}

let args = Array(CommandLine.arguments.dropFirst())
for path in args {
    guard let image = loadImage(path) else {
        print("\(path)\tERR\t0")
        continue
    }
    // The margin is a quarter of the detected height: enough to reach the
    // hairline and the chin, small enough not to reach the collar.
    let probe = detectFace(image, margin: 0)
    guard let rect = probe else {
        print("\(path)\tNOFACE\t0")
        continue
    }
    let margin = rect.height * 0.22
    let grown = detectFace(image, margin: margin)!
    print("\(path)\t\(Int(grown.minX)),\(Int(grown.minY)),\(Int(grown.maxX)),\(Int(grown.maxY))\t"
          + String(format: "%.3f", observation_confidence(image, grown)))
}

func observation_confidence(_ image: CGImage, _ rect: CGRect) -> Double {
    let request = VNDetectFaceRectanglesRequest()
    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    try? handler.perform([request])
    return Double(request.results?.first?.confidence ?? 0)
}
