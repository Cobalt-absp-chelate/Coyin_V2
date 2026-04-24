pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Pdf
import QtQuick.Shapes

Item {
    id: root
    property url documentSource: ""
    property string themeMode: "light"
    property string fitMode: "width"
    property string pageSpread: "single"
    property bool scrollBarsVisible: false
    property string selectedText: ""
    property int currentPageNumber: 0
    readonly property int totalPages: document.pageCount
    readonly property int scalePercent: Math.round(renderScale * 100)
    property real renderScale: 1.0
    readonly property int pagesPerRow: pageSpread === "double" ? 2 : 1
    readonly property real sidePadding: 14
    readonly property real topPadding: 14
    readonly property real rowGap: 10
    readonly property real pageGap: pageSpread === "double" ? 16 : 10
    readonly property real maxPageWidthPoints: {
        var maxWidth = 1
        for (var i = 0; i < document.pageCount; ++i) {
            var size = document.pagePointSize(i)
            maxWidth = Math.max(maxWidth, size.width)
        }
        return maxWidth
    }
    readonly property real maxPageHeightPoints: {
        var maxHeight = 1
        for (var i = 0; i < document.pageCount; ++i) {
            var size = document.pagePointSize(i)
            maxHeight = Math.max(maxHeight, size.height)
        }
        return maxHeight
    }
    readonly property real pageCellWidth: Math.max(1, maxPageWidthPoints * renderScale)

    signal viewStateChanged(var payload)
    signal documentLoadChanged(bool ok)
    signal selectionContextMenuRequested(string text, real globalX, real globalY)
    signal inverseSyncRequested(int page, real x, real y)

    function clampScale(value) {
        return Math.max(0.25, Math.min(value, 4.0))
    }

    function pagePointSize(pageIndex) {
        if (pageIndex < 0 || pageIndex >= document.pageCount)
            return Qt.size(1, 1)
        return document.pagePointSize(pageIndex)
    }

    function pageRect(pageIndex) {
        var item = pageRepeater.itemAt(pageIndex)
        if (!item)
            return null
        var x = contentFlow.x + item.x + item.paperX
        var y = contentFlow.y + item.y
        return Qt.rect(x, y, item.paperWidth, item.paperHeight)
    }

    function estimateCurrentPage() {
        if (document.pageCount <= 0)
            return 0
        var probeX = flick.contentX + flick.width / 2
        var probeY = flick.contentY + Math.max(40, flick.height * 0.35)
        var bestIndex = 0
        var bestScore = Number.MAX_VALUE
        for (var i = 0; i < document.pageCount; ++i) {
            var rect = pageRect(i)
            if (!rect)
                continue
            var dx = 0
            if (probeX < rect.x)
                dx = rect.x - probeX
            else if (probeX > rect.x + rect.width)
                dx = probeX - (rect.x + rect.width)
            var dy = 0
            if (probeY < rect.y)
                dy = rect.y - probeY
            else if (probeY > rect.y + rect.height)
                dy = probeY - (rect.y + rect.height)
            var score = dx * dx + dy * dy * 4
            if (score < bestScore) {
                bestScore = score
                bestIndex = i
            }
        }
        return bestIndex + 1
    }

    function emitState() {
        currentPageNumber = estimateCurrentPage()
        root.viewStateChanged({
            "page": currentPageNumber,
            "totalPages": totalPages,
            "scalePercent": scalePercent,
            "fitMode": fitMode,
            "pageSpread": pageSpread
        })
    }

    function applyFitMode() {
        if (document.status !== PdfDocument.Status.Ready || width <= 0 || height <= 0)
            return
        var availableWidth = Math.max(1, width - sidePadding * 2)
        var availableHeight = Math.max(1, height - topPadding * 2)
        var spreadWidth = pagesPerRow * maxPageWidthPoints + (pagesPerRow - 1) * pageGap
        if (fitMode === "page")
            renderScale = clampScale(Math.min(availableWidth / spreadWidth, availableHeight / maxPageHeightPoints))
        else if (fitMode === "width")
            renderScale = clampScale(availableWidth / spreadWidth)
        emitState()
    }

    function requestState() {
        emitState()
    }

    function pingScrollBars() {
        scrollBarsVisible = true
        scrollBarHideTimer.restart()
    }

    function setScaleMode(mode) {
        fitMode = mode === "page" ? "page" : "width"
        fitTimer.restart()
    }

    function setScalePercent(percent) {
        var targetScale = clampScale(Number(percent) / 100.0)
        if (!Number.isFinite(targetScale))
            return
        fitMode = "custom"
        renderScale = targetScale
        emitState()
    }

    function zoomAroundPoint(point, factor) {
        var oldScale = Math.max(renderScale, 0.0001)
        var targetScale = clampScale(oldScale * factor)
        if (Math.abs(targetScale - oldScale) < 0.0001)
            return
        var contentPoint = Qt.point(flick.contentX + point.x, flick.contentY + point.y)
        var ratio = targetScale / oldScale
        fitMode = "custom"
        renderScale = targetScale
        flick.contentX = contentPoint.x * ratio - point.x
        flick.contentY = contentPoint.y * ratio - point.y
        flick.returnToBounds()
        emitState()
    }

    function setPageSpread(mode) {
        var normalized = mode === "double" ? "double" : "single"
        if (pageSpread === normalized)
            return
        pageSpread = normalized
        if (fitMode !== "custom")
            fitTimer.restart()
        else
            emitState()
    }

    function goToPage(pageNumber) {
        if (!Number.isFinite(pageNumber))
            return
        goToPageIndex(Math.max(0, pageNumber - 1))
    }

    function goToPageIndex(pageIndex) {
        if (!Number.isFinite(pageIndex))
            return
        goToLocationIndex(Math.max(0, pageIndex), 0, 0, 0)
    }

    function goToLocationIndex(pageIndex, x, y, zoom) {
        if (!Number.isFinite(pageIndex))
            return
        if (Number(zoom) > 0) {
            fitMode = "custom"
            renderScale = clampScale(Number(zoom))
        }
        Qt.callLater(function() {
            var rect = pageRect(pageIndex)
            if (!rect)
                return
            var targetX = rect.x + (Number(x) || 0) * renderScale - 24
            var targetY = rect.y + (Number(y) || 0) * renderScale - 24
            flick.contentX = targetX
            flick.contentY = targetY
            flick.returnToBounds()
            emitState()
        })
    }

    function search(text) {
        searchModel.searchString = text || ""
        if (text)
            searchKickTimer.restart()
        if (!text)
            emitState()
    }

    Rectangle {
        anchors.fill: parent
        color: themeMode === "dark" ? "#141b24" : "#eef2f6"
    }

    PdfDocument {
        id: document
        source: root.documentSource
    }

    PdfSearchModel {
        id: searchModel
        document: root.documentSource === undefined ? null : document
        onCurrentResultChanged: {
            if (currentResult >= 0 && currentResultLink)
                root.goToLocationIndex(currentResultLink.page, currentResultLink.location.x, currentResultLink.location.y, 0)
            else
                root.emitState()
        }
    }

    Flickable {
        id: flick
        objectName: "pdfFlick"
        anchors.fill: parent
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        contentWidth: Math.max(width, contentFlow.width + root.sidePadding * 2)
        contentHeight: contentFlow.height + root.topPadding * 2
        onContentXChanged: {
            root.pingScrollBars()
            root.emitState()
        }
        onContentYChanged: {
            root.pingScrollBars()
            root.emitState()
        }

        Flow {
            id: contentFlow
            x: (flick.contentWidth - width) / 2
            y: root.topPadding
            width: root.pagesPerRow * root.pageCellWidth + (root.pagesPerRow - 1) * root.pageGap
            spacing: root.pageGap

            Repeater {
                id: pageRepeater
                model: document.pageCount

                delegate: Item {
                    id: pageHolder
                    required property int index
                    readonly property int pageIndex: index
                    readonly property size pageSize: root.pagePointSize(pageIndex)
                    readonly property real paperWidth: pageSize.width * root.renderScale
                    readonly property real paperHeight: pageSize.height * root.renderScale
                    readonly property real paperX: (width - paperWidth) / 2
                    readonly property real pageScale: paperWidth / Math.max(1, pageSize.width)

                    width: root.pageCellWidth
                    height: paperHeight + root.rowGap

                    Rectangle {
                        id: paper
                        x: pageHolder.paperX
                        y: 0
                        width: pageHolder.paperWidth
                        height: pageHolder.paperHeight
                        color: "#ffffff"
                        border.color: root.themeMode === "dark" ? "#304254" : "#d5dde8"
                        border.width: 1

                        PdfPageImage {
                            id: image
                            anchors.fill: parent
                            document: root.documentSource === undefined ? null : root.document
                            currentFrame: pageHolder.pageIndex
                            asynchronous: true
                            fillMode: Image.PreserveAspectFit
                            sourceSize.width: width * Screen.devicePixelRatio
                            sourceSize.height: 0
                        }

                        Shape {
                            anchors.fill: parent
                            visible: image.status === Image.Ready

                            ShapePath {
                                strokeWidth: -1
                                fillColor: "#f2dca5"
                                scale: Qt.size(pageHolder.pageScale, pageHolder.pageScale)
                                PathMultiline {
                                    paths: searchModel.boundingPolygonsOnPage(pageHolder.pageIndex)
                                }
                            }

                            ShapePath {
                                strokeWidth: searchModel.currentPage === pageHolder.pageIndex ? 2 : 0
                                strokeColor: root.themeMode === "dark" ? "#8eb9de" : "#164e74"
                                fillColor: "transparent"
                                scale: Qt.size(pageHolder.pageScale, pageHolder.pageScale)
                                PathMultiline {
                                    paths: searchModel.currentPage === pageHolder.pageIndex ? searchModel.currentResultBoundingPolygons : []
                                }
                            }

                            ShapePath {
                                strokeWidth: -1
                                fillColor: "#d2c6a066"
                                scale: Qt.size(pageHolder.pageScale, pageHolder.pageScale)
                                PathMultiline {
                                    paths: selection.geometry
                                }
                            }
                        }

                        Repeater {
                            model: PdfLinkModel {
                                document: root.documentSource === undefined ? null : root.document
                                page: pageHolder.pageIndex
                            }

                            delegate: PdfLinkDelegate {
                                x: rectangle.x * pageHolder.pageScale
                                y: rectangle.y * pageHolder.pageScale
                                width: rectangle.width * pageHolder.pageScale
                                height: rectangle.height * pageHolder.pageScale
                                visible: image.status === Image.Ready
                                onTapped: (link) => {
                                    if (link.page >= 0)
                                        root.goToLocationIndex(link.page, link.location.x, link.location.y, link.zoom)
                                    else
                                        Qt.openUrlExternally(url)
                                }
                            }
                        }

                        DragHandler {
                            id: textSelectionDrag
                            acceptedDevices: PointerDevice.Mouse | PointerDevice.Stylus
                            target: null
                        }

                        TapHandler {
                            id: mouseClickHandler
                            acceptedDevices: PointerDevice.Mouse | PointerDevice.Stylus
                        }

                        TapHandler {
                            acceptedButtons: Qt.RightButton
                            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad | PointerDevice.Stylus
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onTapped: function(eventPoint) {
                                if (selection.text.length > 0) {
                                    var localPoint = paper.mapToItem(root, eventPoint.position.x, eventPoint.position.y)
                                    var globalPos = root.mapToGlobal(localPoint)
                                    root.selectionContextMenuRequested(selection.text, globalPos.x, globalPos.y)
                                }
                            }
                        }

                        TapHandler {
                            acceptedButtons: Qt.LeftButton
                            acceptedDevices: PointerDevice.Mouse | PointerDevice.Stylus
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onDoubleTapped: function(eventPoint) {
                                var point = Qt.point(
                                    eventPoint.position.x / Math.max(pageHolder.pageScale, 0.0001),
                                    eventPoint.position.y / Math.max(pageHolder.pageScale, 0.0001)
                                )
                                root.inverseSyncRequested(pageHolder.pageIndex + 1, point.x, point.y)
                            }
                        }

                        PdfSelection {
                            id: selection
                            anchors.fill: parent
                            document: root.documentSource === undefined ? null : root.document
                            page: pageHolder.pageIndex
                            renderScale: Math.max(pageHolder.pageScale, 1.0)
                            from: textSelectionDrag.centroid.pressPosition
                            to: textSelectionDrag.centroid.position
                            hold: !textSelectionDrag.active && !mouseClickHandler.pressed
                            focus: true
                            onTextChanged: {
                                if (text.length > 0)
                                    root.selectedText = text
                                else if (root.selectedText.length > 0)
                                    root.selectedText = ""
                            }
                        }
                    }
                }
            }
        }

        ScrollBar.vertical: ScrollBar {
            id: verticalBar
            policy: ScrollBar.AsNeeded
            width: 12
            opacity: (root.scrollBarsVisible || active || pressed || verticalHover.hovered) ? 1 : 0
            visible: size < 1.0
            contentItem: Rectangle {
                implicitWidth: 8
                radius: 4
                color: root.themeMode === "dark" ? "#8eb9de" : "#164e74"
            }
            background: Rectangle {
                radius: 4
                color: root.themeMode === "dark" ? "#203040" : "#dbe6f1"
                opacity: verticalBar.opacity * 0.28
            }
            Behavior on opacity { NumberAnimation { duration: 180 } }
            HoverHandler { id: verticalHover }
            onPressedChanged: if (pressed) root.pingScrollBars()
            onActiveChanged: if (active) root.pingScrollBars()
        }

        ScrollBar.horizontal: ScrollBar {
            id: horizontalBar
            policy: ScrollBar.AsNeeded
            height: 12
            opacity: (root.scrollBarsVisible || active || pressed || horizontalHover.hovered) ? 1 : 0
            visible: size < 1.0
            contentItem: Rectangle {
                implicitHeight: 8
                radius: 4
                color: root.themeMode === "dark" ? "#8eb9de" : "#164e74"
            }
            background: Rectangle {
                radius: 4
                color: root.themeMode === "dark" ? "#203040" : "#dbe6f1"
                opacity: horizontalBar.opacity * 0.28
            }
            Behavior on opacity { NumberAnimation { duration: 180 } }
            HoverHandler { id: horizontalHover }
            onPressedChanged: if (pressed) root.pingScrollBars()
            onActiveChanged: if (active) root.pingScrollBars()
        }
    }

    Timer {
        id: fitTimer
        interval: 0
        repeat: false
        onTriggered: root.applyFitMode()
    }

    Timer {
        id: searchKickTimer
        interval: 80
        repeat: false
        onTriggered: {
            if (searchModel.searchString.length > 0 && searchModel.count > 0 && searchModel.currentResult < 0)
                searchModel.currentResult = 0
            root.emitState()
        }
    }

    Timer {
        id: scrollBarHideTimer
        interval: 900
        repeat: false
        onTriggered: {
            if (!verticalBar.pressed && !horizontalBar.pressed && !verticalHover.hovered && !horizontalHover.hovered)
                root.scrollBarsVisible = false
        }
    }

    Connections {
        target: document
        function onPageCountChanged() {
            if (root.fitMode !== "custom")
                fitTimer.restart()
            root.emitState()
        }
        function onStatusChanged() {
            root.selectedText = ""
            if (document.status === PdfDocument.Status.Ready) {
                root.documentLoadChanged(true)
                if (root.fitMode !== "custom")
                    fitTimer.restart()
            } else if (document.status === PdfDocument.Status.Error) {
                root.documentLoadChanged(false)
            }
            root.emitState()
        }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        hoverEnabled: true
        onWheel: function(wheel) {
            if (wheel.modifiers & Qt.ControlModifier) {
                root.zoomAroundPoint(Qt.point(wheel.x, wheel.y), wheel.angleDelta.y > 0 ? 1.12 : 1 / 1.12)
                wheel.accepted = true
            } else {
                wheel.accepted = false
            }
            root.pingScrollBars()
        }
        onPositionChanged: function(mouse) {
            const nearRight = width - mouse.x <= 24
            const nearBottom = height - mouse.y <= 24
            if (nearRight || nearBottom)
                root.pingScrollBars()
        }
        onExited: scrollBarHideTimer.restart()
        onPressed: root.pingScrollBars()
        onReleased: root.pingScrollBars()
    }

    HoverHandler {
        id: surfaceHover
        onHoveredChanged: if (hovered) root.pingScrollBars()
    }
}
