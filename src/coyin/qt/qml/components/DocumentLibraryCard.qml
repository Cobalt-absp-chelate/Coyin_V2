import QtQuick
import QtQuick.Controls
import Coyin.Chrome 1.0
import "."
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Rectangle {
    id: root
    property var itemData: ({})
    property var controller: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property bool interactive: true
    readonly property var motion: MotionCore.tokens(root.theme)
    readonly property bool editableDocument: itemData.kind === "draft" || itemData.kind === "markdown" || itemData.kind === "docx"
    readonly property color baseFillColor: MotionCore.cardFill(theme, false, root.enabled, interaction.hovered, interaction.pressed, false)
    readonly property color fillColor: MotionCore.feedbackShade(
        MotionCore.mixColor(baseFillColor, theme.accentSurface, interaction.accentStrength * 0.10 + interaction.settleStrength * 0.06),
        theme,
        interaction.hoverProgress,
        interaction.pressProgress,
        0,
        interaction.focusProgress
    )
    readonly property color borderTone: MotionCore.cardBorder(theme, false, root.enabled, interaction.hovered, interaction.pressed, false)
    readonly property color frameColor: MotionCore.mixColor(borderTone, theme.anchor, interaction.frameStrength * 0.24)
    readonly property real surfaceScale: MotionCore.surfaceScale(interaction.hoverProgress, interaction.focusProgress, interaction.pressProgress, interaction.settleStrength, true)

    radius: motion.radiusMedium
    color: root.enabled ? root.fillColor : theme.panel
    border.color: root.enabled ? root.frameColor : theme.border
    border.width: 1
    implicitHeight: infoColumn.implicitHeight + 28
    scale: root.surfaceScale
    transformOrigin: Item.Center

    Behavior on color {
        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
    }

    Behavior on border.color {
        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
    }

    Behavior on scale {
        NumberAnimation { duration: MotionCore.duration("panel", root.theme); easing.type: Easing.OutCubic }
    }

    InteractionTracker {
        id: interaction
        targetItem: root
        hoverTrackingEnabled: false
        cursorShape: Qt.PointingHandCursor
        interactive: root.interactive
        hoveredInputOverride: clickArea.containsMouse
        pressedInputOverride: clickArea.pressed
    }

    SignalAccent {
        anchors.fill: parent
        active: interaction.accentStrength > 0.18
        hovered: interaction.hovered
        pressed: interaction.pressed
        accentColor: theme.anchor
        neutralColor: theme.accentSoft
        edge: "frame"
        radius: motion.radiusMedium
    }

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 4
        color: MotionCore.mixColor(itemData.group_color || theme.borderStrong, theme.anchor, interaction.textStrength * 0.18)

        Behavior on color {
            ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
        }
    }

    Column {
        id: infoColumn
        anchors.left: parent.left
        anchors.leftMargin: 18
        anchors.right: parent.right
        anchors.rightMargin: 18
        anchors.verticalCenter: parent.verticalCenter
        spacing: 8

        Text {
            text: itemData.display_title
            color: MotionCore.mixColor(theme.text, theme.anchor, interaction.textStrength * 0.26)
            font.pixelSize: 16
            font.weight: Font.DemiBold
            elide: Text.ElideRight
            width: parent.width

            Behavior on color {
                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
            }
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
            color: MotionCore.mixColor(theme.textMuted, theme.textSoft, interaction.textStrength * 0.36)
            width: parent.width
            elide: Text.ElideRight

            Behavior on color {
                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
            }
        }

        Rectangle {
            width: parent.width
            color: MotionCore.mixColor(theme.panelInset, theme.panelFocus, interaction.frameStrength * 0.44 + interaction.settleStrength * 0.08)
            border.color: MotionCore.mixColor(theme.border, theme.accentOutline, interaction.frameStrength * 0.54 + interaction.settleStrength * 0.14)
            border.width: 1
            radius: motion.radiusSmall
            implicitHeight: 56

            Behavior on color {
                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
            }

            Behavior on border.color {
                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
            }

            Text {
                anchors.fill: parent
                anchors.margins: 10
                text: itemData.excerpt || "尚未生成摘要摘录。"
                color: MotionCore.mixColor(theme.textSoft, theme.textMuted, interaction.textStrength * 0.42)
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight

                Behavior on color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }
            }
        }

        Text {
            width: parent.width
            text: "左键打开 · 右键菜单"
            color: MotionCore.mixColor(theme.textSoft, theme.textMuted, interaction.textStrength * 0.24)
            font.pixelSize: 10
            horizontalAlignment: Text.AlignRight
        }
    }

    Menu {
        id: contextMenu

        MenuItem {
            text: root.editableDocument ? "打开编辑" : "打开阅读"
            onTriggered: if (controller) controller.openDocument(itemData.document_id)
        }
        MenuItem {
            text: "分析"
            onTriggered: if (controller) controller.analyzeDocument(itemData.document_id)
        }
        MenuSeparator {}
        MenuItem {
            text: itemData.favorite ? "取消收藏" : "收藏"
            onTriggered: if (controller) controller.toggleDocumentFavorite(itemData.document_id)
        }
        MenuItem {
            text: "重命名"
            onTriggered: if (controller) controller.promptRenameDocument(itemData.document_id)
        }
        MenuItem {
            text: "删除"
            onTriggered: if (controller) controller.deleteDocument(itemData.document_id)
        }
    }

    MouseArea {
        id: clickArea
        anchors.fill: parent
        enabled: root.visible && root.interactive
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: function(mouse) {
            if (mouse.button === Qt.LeftButton) {
                if (controller)
                    controller.openDocument(itemData.document_id)
                return
            }
            if (mouse.button === Qt.RightButton) {
                contextMenu.x = mouse.x + 4
                contextMenu.y = mouse.y + 4
                contextMenu.open()
            }
        }
    }
}
