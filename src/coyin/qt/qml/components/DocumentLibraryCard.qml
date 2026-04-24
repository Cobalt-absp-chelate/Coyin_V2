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
    readonly property var motion: MotionCore.tokens(root.theme)

    radius: motion.radiusMedium
    color: root.enabled
           ? MotionCore.mixColor(theme.panelRaised, MotionCore.mixColor(theme.panelHover, theme.accentSurface, 0.24 + interaction.settleStrength * 0.14), interaction.frameStrength)
           : theme.panel
    border.color: root.enabled
                  ? MotionCore.mixColor(theme.border, theme.accentOutline, interaction.frameStrength * 0.76 + interaction.settleStrength * 0.18)
                  : theme.border
    border.width: 1
    implicitHeight: Math.max(infoColumn.implicitHeight, actions.implicitHeight) + 28

    Behavior on color {
        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
    }

    Behavior on border.color {
        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
    }

    InteractionState {
        id: interaction
        enabledInput: root.enabled
        visibleInput: root.visible
        hoveredInput: hoverHandler.hovered
        pressedInput: false
        focusedInput: false
        busyInput: false
        selectedInput: false
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

    HoverHandler {
        id: hoverHandler
        enabled: root.visible
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
        anchors.right: actions.left
        anchors.rightMargin: 16
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10

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
