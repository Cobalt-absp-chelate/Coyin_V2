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
    implicitHeight: Math.max(infoColumn.implicitHeight, actions.implicitHeight) + 28

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
        color: itemData.group_color
    }

    Column {
        id: infoColumn
        anchors.left: parent.left
        anchors.leftMargin: 18
        anchors.right: actions.left
        anchors.rightMargin: 16
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10

        Text {
            text: itemData.display_title
            color: theme.text
            font.pixelSize: 16
            font.weight: Font.DemiBold
            elide: Text.ElideRight
            width: parent.width
        }

        Row {
            spacing: 8
            InfoPill { text: itemData.kind_label; fillColor: theme.panelInset; borderColor: theme.border; textColor: theme.textMuted }
            InfoPill { text: itemData.year || "年份未标注"; fillColor: theme.panelInset; borderColor: theme.border; textColor: theme.textMuted }
            InfoPill { text: itemData.progress + "%"; fillColor: theme.accentSurface; borderColor: theme.accentOutline; textColor: theme.anchor }
            InfoPill { text: itemData.favorite ? "已收藏" : "未收藏"; fillColor: itemData.favorite ? theme.accentSurface : theme.panelInset; borderColor: itemData.favorite ? theme.accentOutline : theme.border; textColor: itemData.favorite ? theme.anchor : theme.textMuted }
        }

        Text {
            text: (itemData.authors || "未标注作者") + (itemData.metadata_summary ? "  ·  " + itemData.metadata_summary : "")
            color: theme.textMuted
            width: parent.width
            elide: Text.ElideRight
        }

        Rectangle {
            width: parent.width
            color: theme.panelInset
            border.color: theme.border
            border.width: 1
            radius: 4
            implicitHeight: 56

            Text {
                anchors.fill: parent
                anchors.margins: 10
                text: itemData.excerpt || "尚未生成摘要摘录。"
                color: theme.textSoft
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
        }
    }

    Column {
        id: actions
        anchors.right: parent.right
        anchors.rightMargin: 14
        anchors.verticalCenter: parent.verticalCenter
        spacing: 8

        InteractiveButton { theme: root.theme; text: "阅读"; onClicked: if (controller) controller.openDocument(itemData.document_id) }
        InteractiveButton { theme: root.theme; text: "分析"; onClicked: if (controller) controller.analyzeDocument(itemData.document_id) }
        InteractiveButton { theme: root.theme; text: "草稿"; onClicked: if (controller) controller.createDraftFromDocument(itemData.document_id) }
        InteractiveButton { theme: root.theme; text: itemData.favorite ? "取消收藏" : "收藏"; selected: itemData.favorite; onClicked: if (controller) controller.toggleDocumentFavorite(itemData.document_id) }
        InteractiveButton { theme: root.theme; text: "重命名"; onClicked: if (controller) controller.promptRenameDocument(itemData.document_id) }
    }
}
