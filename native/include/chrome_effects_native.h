#pragma once

#include <QColor>
#include <QEasingCurve>
#include <QElapsedTimer>
#include <QPointer>
#include <QQuickItem>
#include <QTimer>

class QQuickWindow;
class QSGNode;

class SignalAccentItem : public QQuickItem
{
    Q_OBJECT
    Q_PROPERTY(bool active READ active WRITE setActive NOTIFY activeChanged FINAL)
    Q_PROPERTY(bool hovered READ hovered WRITE setHovered NOTIFY hoveredChanged FINAL)
    Q_PROPERTY(bool pressed READ pressed WRITE setPressed NOTIFY pressedChanged FINAL)
    Q_PROPERTY(QColor accentColor READ accentColor WRITE setAccentColor NOTIFY accentColorChanged FINAL)
    Q_PROPERTY(QColor neutralColor READ neutralColor WRITE setNeutralColor NOTIFY neutralColorChanged FINAL)
    Q_PROPERTY(QString edge READ edge WRITE setEdge NOTIFY edgeChanged FINAL)
    Q_PROPERTY(qreal radius READ radius WRITE setRadius NOTIFY radiusChanged FINAL)

public:
    explicit SignalAccentItem(QQuickItem *parent = nullptr);

    bool active() const;
    void setActive(bool value);

    bool hovered() const;
    void setHovered(bool value);

    bool pressed() const;
    void setPressed(bool value);

    QColor accentColor() const;
    void setAccentColor(const QColor &value);

    QColor neutralColor() const;
    void setNeutralColor(const QColor &value);

    QString edge() const;
    void setEdge(const QString &value);

    qreal radius() const;
    void setRadius(qreal value);

    void itemChange(ItemChange change, const ItemChangeData &value) override;

signals:
    void activeChanged();
    void hoveredChanged();
    void pressedChanged();
    void accentColorChanged();
    void neutralColorChanged();
    void edgeChanged();
    void radiusChanged();

private slots:
    void tickAnimation();
    void onWindowChanged(QQuickWindow *window);
    void onWindowActiveChanged();
    void onVisibleOrEnabledChanged();

private:
    qreal targetProgress() const;
    void animate();
    void clearInteraction();
    QSGNode *updatePaintNode(QSGNode *oldNode, UpdatePaintNodeData *updatePaintNodeData) override;
    void geometryChange(const QRectF &newGeometry, const QRectF &oldGeometry) override;

    bool m_active = false;
    bool m_hovered = false;
    bool m_pressed = false;
    QString m_edge = QStringLiteral("left");
    qreal m_radius = 6.0;
    QColor m_accent = QColor(QStringLiteral("#1f5a84"));
    QColor m_neutral = QColor(QStringLiteral("#dbe8f3"));
    qreal m_progress = 0.0;
    qreal m_fromProgress = 0.0;
    qreal m_toProgress = 0.0;
    int m_durationMs = 220;
    QEasingCurve m_curve = QEasingCurve(QEasingCurve::InOutCubic);
    QElapsedTimer m_clock;
    QTimer m_timer;
    QPointer<QQuickWindow> m_window;
};

class ShimmerRailItem : public QQuickItem
{
    Q_OBJECT
    Q_PROPERTY(bool running READ running WRITE setRunning NOTIFY runningChanged FINAL)
    Q_PROPERTY(QColor accentColor READ accentColor WRITE setAccentColor NOTIFY accentColorChanged FINAL)
    Q_PROPERTY(QColor baseColor READ baseColor WRITE setBaseColor NOTIFY baseColorChanged FINAL)
    Q_PROPERTY(qreal radius READ radius WRITE setRadius NOTIFY radiusChanged FINAL)

public:
    explicit ShimmerRailItem(QQuickItem *parent = nullptr);

    bool running() const;
    void setRunning(bool value);

    QColor accentColor() const;
    void setAccentColor(const QColor &value);

    QColor baseColor() const;
    void setBaseColor(const QColor &value);

    qreal radius() const;
    void setRadius(qreal value);

signals:
    void runningChanged();
    void accentColorChanged();
    void baseColorChanged();
    void radiusChanged();

private slots:
    void tick();
    void updateTimerState();

private:
    QSGNode *updatePaintNode(QSGNode *oldNode, UpdatePaintNodeData *updatePaintNodeData) override;
    void geometryChange(const QRectF &newGeometry, const QRectF &oldGeometry) override;

    bool m_running = true;
    qreal m_phase = 0.0;
    qreal m_radius = 6.0;
    QColor m_accent = QColor(QStringLiteral("#1f5a84"));
    QColor m_base = QColor(QStringLiteral("#dbe8f3"));
    QTimer m_timer;
};

class InteractionStateItem : public QQuickItem
{
    Q_OBJECT
    Q_PROPERTY(QString resolvedState READ resolvedState NOTIFY resolvedStateChanged FINAL)
    Q_PROPERTY(bool active READ active NOTIFY activeChanged FINAL)
    Q_PROPERTY(bool hovered READ hovered NOTIFY hoveredChanged FINAL)
    Q_PROPERTY(bool pressed READ pressed NOTIFY pressedChanged FINAL)
    Q_PROPERTY(bool focused READ focused NOTIFY focusedChanged FINAL)
    Q_PROPERTY(qreal hoverProgress READ hoverProgress NOTIFY hoverProgressChanged FINAL)
    Q_PROPERTY(qreal pressProgress READ pressProgress NOTIFY pressProgressChanged FINAL)
    Q_PROPERTY(qreal focusProgress READ focusProgress NOTIFY focusProgressChanged FINAL)
    Q_PROPERTY(qreal selectionProgress READ selectionProgress NOTIFY selectionProgressChanged FINAL)
    Q_PROPERTY(qreal busyProgress READ busyProgress NOTIFY busyProgressChanged FINAL)
    Q_PROPERTY(qreal engageProgress READ engageProgress NOTIFY engageProgressChanged FINAL)
    Q_PROPERTY(qreal accentStrength READ accentStrength NOTIFY visualProgressChanged FINAL)
    Q_PROPERTY(qreal frameStrength READ frameStrength NOTIFY visualProgressChanged FINAL)
    Q_PROPERTY(qreal textStrength READ textStrength NOTIFY visualProgressChanged FINAL)
    Q_PROPERTY(qreal settleStrength READ settleStrength NOTIFY visualProgressChanged FINAL)
    Q_PROPERTY(bool enabledInput READ enabledInput WRITE setEnabledInput NOTIFY enabledInputChanged FINAL)
    Q_PROPERTY(bool visibleInput READ visibleInput WRITE setVisibleInput NOTIFY visibleInputChanged FINAL)
    Q_PROPERTY(bool hoveredInput READ hoveredInput WRITE setHoveredInput NOTIFY hoveredInputChanged FINAL)
    Q_PROPERTY(bool pressedInput READ pressedInput WRITE setPressedInput NOTIFY pressedInputChanged FINAL)
    Q_PROPERTY(bool focusedInput READ focusedInput WRITE setFocusedInput NOTIFY focusedInputChanged FINAL)
    Q_PROPERTY(bool busyInput READ busyInput WRITE setBusyInput NOTIFY busyInputChanged FINAL)
    Q_PROPERTY(bool selectedInput READ selectedInput WRITE setSelectedInput NOTIFY selectedInputChanged FINAL)

public:
    explicit InteractionStateItem(QQuickItem *parent = nullptr);

    QString resolvedState() const;
    bool active() const;
    bool hovered() const;
    bool pressed() const;
    bool focused() const;
    qreal hoverProgress() const;
    qreal pressProgress() const;
    qreal focusProgress() const;
    qreal selectionProgress() const;
    qreal busyProgress() const;
    qreal engageProgress() const;
    qreal accentStrength() const;
    qreal frameStrength() const;
    qreal textStrength() const;
    qreal settleStrength() const;

    bool enabledInput() const;
    void setEnabledInput(bool value);

    bool visibleInput() const;
    void setVisibleInput(bool value);

    bool hoveredInput() const;
    void setHoveredInput(bool value);

    bool pressedInput() const;
    void setPressedInput(bool value);

    bool focusedInput() const;
    void setFocusedInput(bool value);

    bool busyInput() const;
    void setBusyInput(bool value);

    bool selectedInput() const;
    void setSelectedInput(bool value);

signals:
    void resolvedStateChanged();
    void activeChanged();
    void hoveredChanged();
    void pressedChanged();
    void focusedChanged();
    void hoverProgressChanged();
    void pressProgressChanged();
    void focusProgressChanged();
    void selectionProgressChanged();
    void busyProgressChanged();
    void engageProgressChanged();
    void visualProgressChanged();
    void enabledInputChanged();
    void visibleInputChanged();
    void hoveredInputChanged();
    void pressedInputChanged();
    void focusedInputChanged();
    void busyInputChanged();
    void selectedInputChanged();

private slots:
    void onWindowChanged(QQuickWindow *window);
    void updateState();
    void tickAnimation();

private:
    bool windowActive() const;
    QString computeState() const;
    void animateProgresses();

    bool m_enabledInput = true;
    bool m_visibleInput = true;
    bool m_hoveredInput = false;
    bool m_pressedInput = false;
    bool m_focusedInput = false;
    bool m_busyInput = false;
    bool m_selectedInput = false;
    QString m_resolvedState = QStringLiteral("normal");
    QPointer<QQuickWindow> m_window;
    qreal m_hoverProgress = 0.0;
    qreal m_hoverFrom = 0.0;
    qreal m_hoverTo = 0.0;
    qreal m_pressProgress = 0.0;
    qreal m_pressFrom = 0.0;
    qreal m_pressTo = 0.0;
    qreal m_focusProgress = 0.0;
    qreal m_focusFrom = 0.0;
    qreal m_focusTo = 0.0;
    qreal m_selectionProgress = 0.0;
    qreal m_selectionFrom = 0.0;
    qreal m_selectionTo = 0.0;
    qreal m_busyProgress = 0.0;
    qreal m_busyFrom = 0.0;
    qreal m_busyTo = 0.0;
    qreal m_engageProgress = 0.0;
    qreal m_engageFrom = 0.0;
    qreal m_engageTo = 0.0;
    int m_animationDurationMs = 150;
    QEasingCurve m_animationCurve = QEasingCurve(QEasingCurve::InOutCubic);
    QElapsedTimer m_animationClock;
    QTimer m_animationTimer;
};

class DisclosureMotionItem : public QQuickItem
{
    Q_OBJECT
    Q_PROPERTY(bool expanded READ expanded WRITE setExpanded NOTIFY expandedChanged FINAL)
    Q_PROPERTY(qreal progress READ progress NOTIFY progressChanged FINAL)
    Q_PROPERTY(int duration READ duration WRITE setDuration NOTIFY durationChanged FINAL)

public:
    explicit DisclosureMotionItem(QQuickItem *parent = nullptr);

    bool expanded() const;
    void setExpanded(bool value);

    qreal progress() const;

    int duration() const;
    void setDuration(int value);

signals:
    void expandedChanged();
    void progressChanged();
    void durationChanged();

private slots:
    void tick();

private:
    void animate();

    bool m_expanded = false;
    qreal m_progress = 0.0;
    qreal m_fromProgress = 0.0;
    qreal m_toProgress = 0.0;
    int m_durationMs = 190;
    QEasingCurve m_curve = QEasingCurve(QEasingCurve::InOutCubic);
    QElapsedTimer m_clock;
    QTimer m_timer;
};

extern "C" __declspec(dllexport) int coyin_register_qml_types();
