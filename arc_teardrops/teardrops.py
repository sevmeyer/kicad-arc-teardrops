# Arc teardrops plugin for KiCad 7
# https://github.com/sevmeyer/kicad-arc-teardrops

import math
import pcbnew


def addArcTeardrops(relRadiusPTH, relRadiusSMD, relRadiusVIA):
    board = pcbnew.GetBoard()
    group = getGroup(board, "ARC-TEARDROPS")
    tracks = getAllTracks(board)
    count = 0

    if relRadiusPTH > 0:
        pads = getSelectedPads(board, pcbnew.PAD_ATTRIB_PTH)
        count += addArcs(board, group, tracks, pads, relRadiusPTH)

    if relRadiusSMD > 0:
        pads = getSelectedPads(board, pcbnew.PAD_ATTRIB_SMD)
        count += addArcs(board, group, tracks, pads, relRadiusSMD)

    if relRadiusVIA > 0:
        pads = getSelectedVias(board)
        count += addArcs(board, group, tracks, pads, relRadiusVIA)

    return count


def getGroup(board, name):
    for group in board.Groups():
        if group.GetName() == name:
            return group
    group = pcbnew.PCB_GROUP(board)
    group.SetName(name)
    board.Add(group)
    return group


def getAllTracks(board):
    return [t for t in board.GetTracks()
        if type(t) is pcbnew.PCB_TRACK]


def getSelectedPads(board, attribute):
    return [GenericPad(p) for p in board.GetPads()
        if p.IsSelected() and p.GetAttribute() == attribute]


def getSelectedVias(board):
    return [GenericPad.fromVia(board, v) for v in board.GetTracks()
        if v.IsSelected() and type(v) is pcbnew.PCB_VIA]


def addArcs(board, group, tracks, pads, relRadius):
    count = 0

    for pad in pads:
        for track in tracks:
            trackLayer = track.GetLayer()
            trackWidth = track.GetWidth()
            trackStart = track.GetStart()
            trackEnd = track.GetEnd()
            absRadius = int(trackWidth*relRadius + 0.5)

            if not pad.layerSet.Contains(trackLayer):
                continue

            containsStart = pad.polySet.Contains(trackStart)
            containsEnd = pad.polySet.Contains(trackEnd)

            if containsStart and not containsEnd:
                trackSeg = pcbnew.SEG(trackStart, trackEnd)
            elif containsEnd and not containsStart:
                trackSeg = pcbnew.SEG(trackEnd, trackStart)
            else:
                continue

            padToArcEnd = -trackWidth//2
            padToArcCenter = padToArcEnd + absRadius

            if padToArcCenter <= 0:
                continue

            def addArc(sign):
                trackDir = trackSeg.B - trackSeg.A
                trackOrtho = trackDir.Perpendicular().Resize(absRadius)
                trackOffset = trackSeg.ParallelSeg(trackSeg.A + trackOrtho*sign)
                padOffset = pad.getOffset(padToArcCenter)
                intersections = getIntersections(padOffset, trackOffset)

                if len(intersections) != 1:
                    return 0

                center = intersections[0]
                start = trackSeg.NearestPoint(center)
                end = pad.getOffset(padToArcEnd).NearestPoint(center)

                if trackSeg.LineDistance(end) < trackWidth/100:
                    return 0

                mid = center + ((start + end)/2 - center).Resize(absRadius)
                arc = pcbnew.PCB_ARC(board)
                arc.SetLayer(trackLayer)
                arc.SetWidth(trackWidth)
                arc.SetStart(start if sign < 0 else end)
                arc.SetMid(mid)
                arc.SetEnd(end if sign < 0 else start)
                board.Add(arc)
                group.AddItem(arc)
                return 1

            count += addArc(1)
            count += addArc(-1)

    return count


class GenericPad():

    def __init__(self, pad):
        self.layerSet = pad.GetLayerSet()
        self.polySet = pad.GetEffectivePolygon()
        self.offsetCache = {}

    @staticmethod
    def fromVia(board, via):
        # It doesn't seem possible to use PCB_VIA.TransformShapeToPolygon()
        foot = pcbnew.FOOTPRINT(board)
        pad = pcbnew.PAD(foot)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(pcbnew.VECTOR2I(via.GetWidth(), via.GetWidth()))
        pad.SetPosition(via.GetCenter())
        pad.SetLayerSet(via.GetLayerSet())
        return GenericPad(pad)

    def getOffset(self, amount):
        if amount not in self.offsetCache:
            copy = pcbnew.SHAPE_POLY_SET(self.polySet)
            copy.Inflate(amount, 32)
            self.offsetCache[amount] = copy
        return self.offsetCache[amount].COutline(0)


def getIntersections(lineChain, seg):
    # It doesn't seem possible to use SHAPE_LINE_CHAIN.Intersect(),
    # hence a bit of improvisation.

    def intersect(a, b, c, d):
        # Intersection point of two line segments in 2 dimensions - Paul Bourke
        # http://paulbourke.net/geometry/pointlineplane/
        denom = (d.y - c.y)*(b.x - a.x) - (d.x - c.x)*(b.y - a.y)
        if abs(denom) > 1e-6:
            abPos = ((d.x - c.x)*(a.y - c.y) - (d.y - c.y)*(a.x - c.x)) / denom
            cdPos = ((b.x - a.x)*(a.y - c.y) - (b.y - a.y)*(a.x - c.x)) / denom
            if 0 <= abPos <= 1 and 0 <= cdPos <= 1:
                return pcbnew.VECTOR2I(
                    int(a.x + (b.x - a.x)*abPos + 0.5),
                    int(a.y + (b.y - a.y)*abPos + 0.5))
        return None

    points = []
    for s in range(lineChain.SegmentCount()):
        # It doesn't seem possible to unpack OPT_VECTOR2I from SEG.Intersect()
        chainSeg = lineChain.CSegment(s)
        point = intersect(chainSeg.A, chainSeg.B, seg.A, seg.B)
        if point is not None and point not in points:
            points.append(point)
    return points
