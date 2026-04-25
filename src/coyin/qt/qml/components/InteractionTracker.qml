import QtQuick
import QtQuick.Window
import Coyin.Chrome 1.0

Item {
    id: root

    property Item targetItem: parent
    property bool interactive: true
    property bool tapEnabled: false
    property bool hoverTrackingEnabled: interactive
    property bool cursorEnabled: true
    property bool busy: false
    property bool selected: false
    property bool focusedInput: false
    property bool hoveredInputOverride: false
    property bool pressedInputOverride: false
    property bool enabledInput: root.enabled && (!root.targetItem || root.targetItem.enabled === undefined || root.targetItem.enabled)
    property bool visibleInput: root.visible && (!root.targetItem || root.targetItem.visible === undefined || root.targetItem.visible)
    property int cursorShape: Qt.PointingHandCursor
    property int acceptedButtons: Qt.LeftButton
    property int extraResetToken: 0

    readonly property int sharedResetToken: {
        var hostWindow = Window.window
        if (!hostWindow)
            return 0
        return hostWindow.interactionResetToken !== undefined ? hostWindow.interactionResetToken : 0
    }
    readonly property alias state: interaction
    readonly property bool hovered: interaction.hovered
    readonly property bool pressed: interaction.pressed
    readonly property bool active: interaction.active
    readonly property bool focused: interaction.focused
    readonly property real hoverProgress: interaction.hoverProgress
    readonly property real pressProgress: interaction.pressProgress
    readonly property real focusProgress: interaction.focusProgress
    readonly property real selectionProgress: interaction.selectionProgress
    readonly property real busyProgress: interaction.busyProgress
    readonly property real engageProgress: interaction.engageProgress
    readonly property real accentStrength: interaction.accentStrength
    readonly property real frameStrength: interaction.frameStrength
    readonly property real textStrength: interaction.textStrength
    readonly property real settleStrength: interaction.settleStrength

    signal tapped(var eventPoint)

    anchors.fill: parent
    visible: true
    enabled: true
    z: 1000

    InteractionState {
        id: interaction
        targetItem: root.targetItem ? root.targetItem : root.parent
        resetToken: root.sharedResetToken + root.extraResetToken
        enabledInput: root.enabledInput
        visibleInput: root.visibleInput
        hoveredInput: hoverCursor.hovered || root.hoveredInputOverride
        pressedInput: tapHandler.active || root.pressedInputOverride
        focusedInput: root.focusedInput
        busyInput: root.busy
        selectedInput: root.selected
    }

    HoverHandler {
        id: hoverCursor
        enabled: root.interactive && root.hoverTrackingEnabled && root.enabledInput && root.visibleInput && !root.busy
        cursorShape: root.cursorEnabled ? root.cursorShape : undefined
    }

    TapHandler {
        id: tapHandler
        enabled: root.interactive && root.tapEnabled && root.enabledInput && root.visibleInput && !root.busy
        acceptedButtons: root.acceptedButtons
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: function(eventPoint) { root.tapped(eventPoint) }
    }
}
