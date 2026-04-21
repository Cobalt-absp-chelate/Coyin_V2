import QtQuick
import QtQuick.Controls
import Coyin.Chrome 1.0
import "."
import "../support/UiDefaults.js" as UiDefaults

Rectangle {
    id: root
    property var itemData: ({})
    property var controller: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())

    radius: 6
    color: theme.panelRaised
    border.color: theme.border
    border.width: 1
    implicitHeight: Math.max(infoColumn.implicitHeight, actionColumn.implicitHeight) + 28

    SignalAccent {
        anchors.fill: parent
        active: false
        hovered: hover.containsMouse
        pressed: false
        accentColor: theme.anchor
        neutralColor: theme.accentSoft
        edge: "frame"
        radius: 6
    }

    MouseArea {
        id: hover
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 4
        color: theme.anchor
    }

    Column {
        id: infoColumn
        anchors.left: parent.left
        anchors.leftMargin: 18
        anchors.right: actionColumn.left
        anchors.rightMargin: 16
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10

        Row {
            spacing: 8
            InfoPill { text: itemData.source_label; fillColor: theme.accentSurface; borderColor: theme.accentOutline; textColor: theme.anchor }
            InfoPill { text: itemData.year; fillColor: theme.panelInset; borderColor: theme.border; textColor: theme.textMuted }
            InfoPill { text: itemData.item_type; fillColor: theme.panelInset; borderColor: theme.border; textColor: theme.textMuted }
        }

        Text {
            text: itemData.title
            color: theme.text
            font.pixelSize: 16
            font.weight: Font.DemiBold
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
            width: parent.width
        }

        Text {
            text: itemData.authors
            color: theme.textMuted
            width: parent.width
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }

        Rectangle {
            width: parent.width
            color: theme.panelInset
            border.color: theme.border
            border.width: 1
            radius: 4
            implicitHeight: 64

            Text {
                anchors.fill: parent
                anchors.margins: 10
                text: itemData.abstract_text
                color: theme.textSoft
                width: parent.width
                wrapMode: Text.Wrap
                maximumLineCount: 3
                elide: Text.ElideRight
            }
        }

        Text {
            visible: !!itemData.meta_summary
            text: itemData.meta_summary
            color: theme.textSoft
            font.pixelSize: 11
            width: parent.width
            elide: Text.ElideRight
        }

        Text {
            text: itemData.status_line
            color: theme.anchor
            font.pixelSize: 11
            width: parent.width
            elide: Text.ElideRight
        }
    }

    Column {
        id: actionColumn
        anchors.right: parent.right
        anchors.rightMargin: 14
        anchors.verticalCenter: parent.verticalCenter
        spacing: 8

        InteractiveButton { theme: root.theme; text: "打开原页"; onClicked: if (controller) controller.openSearchResultLink(itemData.result_id) }
        InteractiveButton { theme: root.theme; text: itemData.has_pdf ? "下载 PDF" : "下载"; onClicked: if (controller) controller.downloadSearchResult(itemData.result_id) }
        InteractiveButton { theme: root.theme; text: "加入资料库"; onClicked: if (controller) controller.addSearchResultToLibrary(itemData.result_id) }
        InteractiveButton { theme: root.theme; text: "入库并分析"; tone: "accent"; onClicked: if (controller) controller.addSearchResultToLibraryAndAnalyze(itemData.result_id) }
    }
}
