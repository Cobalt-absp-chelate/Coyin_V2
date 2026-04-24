#include "chrome_effects_native.h"

#include <algorithm>
#include <cmath>
#include <cstring>

#include <QMatrix4x4>
#include <QPointer>
#include <QQuickWindow>
#include <QSGGeometry>
#include <QSGGeometryNode>
#include <QSGMaterial>
#include <QSGMaterialShader>
#include <QTimer>
#include <QVector4D>
#include <QWindow>
#include <qqml.h>

namespace {

constexpr int kUniformBlockSize = 144;

QVector4D colorVector(const QColor &color)
{
    return QVector4D(color.redF(), color.greenF(), color.blueF(), color.alphaF());
}

void writeMatrix(QByteArray *uniformData, int offset, const QMatrix4x4 &matrix)
{
    std::memcpy(uniformData->data() + offset, matrix.constData(), sizeof(float) * 16);
}

void writeVector(QByteArray *uniformData, int offset, const QVector4D &vector)
{
    const float values[] = { vector.x(), vector.y(), vector.z(), vector.w() };
    std::memcpy(uniformData->data() + offset, values, sizeof(values));
}

float edgeTypeForString(const QString &edge)
{
    if (edge == QLatin1String("right")) {
        return 1.0f;
    }
    if (edge == QLatin1String("bottom")) {
        return 2.0f;
    }
    if (edge == QLatin1String("top")) {
        return 3.0f;
    }
    if (edge == QLatin1String("frame")) {
        return 4.0f;
    }
    return 0.0f;
}

int compareFloat(qreal left, qreal right)
{
    if (left < right) {
        return -1;
    }
    if (left > right) {
        return 1;
    }
    return 0;
}

int compareColor(const QColor &left, const QColor &right)
{
    const QRgb leftValue = left.rgba();
    const QRgb rightValue = right.rgba();
    if (leftValue < rightValue) {
        return -1;
    }
    if (leftValue > rightValue) {
        return 1;
    }
    return 0;
}

class SharedAnimationDriver final
{
public:
    static SharedAnimationDriver &instance()
    {
        static SharedAnimationDriver driver;
        return driver;
    }

    template<typename Receiver, typename Slot>
    void activate(Receiver *receiver, Slot slot)
    {
        if (!receiver) {
            return;
        }
        purge();
        for (const auto &entry : m_entries) {
            if (entry.target == receiver) {
                return;
            }
        }

        Entry entry;
        entry.target = receiver;
        entry.connection = QObject::connect(&m_timer, &QTimer::timeout, receiver, slot);
        m_entries.push_back(entry);
        updateTimerState();
    }

    void deactivate(QObject *receiver)
    {
        if (!receiver) {
            return;
        }
        bool removed = false;
        for (auto it = m_entries.begin(); it != m_entries.end();) {
            if (it->target == receiver || it->target.isNull()) {
                QObject::disconnect(it->connection);
                it = m_entries.erase(it);
                removed = true;
            } else {
                ++it;
            }
        }
        if (removed) {
            updateTimerState();
        }
    }

private:
    struct Entry
    {
        QPointer<QObject> target;
        QMetaObject::Connection connection;
    };

    SharedAnimationDriver()
    {
        m_timer.setInterval(16);
        m_timer.setTimerType(Qt::PreciseTimer);
    }

    void purge()
    {
        bool removed = false;
        for (auto it = m_entries.begin(); it != m_entries.end();) {
            if (it->target.isNull()) {
                QObject::disconnect(it->connection);
                it = m_entries.erase(it);
                removed = true;
            } else {
                ++it;
            }
        }
        if (removed) {
            updateTimerState();
        }
    }

    void updateTimerState()
    {
        if (m_entries.empty()) {
            m_timer.stop();
        } else if (!m_timer.isActive()) {
            m_timer.start();
        }
    }

    QTimer m_timer;
    std::vector<Entry> m_entries;
};

class AccentMaterialShader final : public QSGMaterialShader
{
public:
    AccentMaterialShader()
    {
        setShaderFileName(VertexStage, QStringLiteral(":/coyin/chrome/shaders/surface.vert.qsb"));
        setShaderFileName(FragmentStage, QStringLiteral(":/coyin/chrome/shaders/signal_accent.frag.qsb"));
    }

    bool updateUniformData(RenderState &state, QSGMaterial *newMaterial, QSGMaterial *) override;
};

class AccentMaterial final : public QSGMaterial
{
public:
    AccentMaterial()
    {
        setFlag(Blending, true);
    }

    QSGMaterialType *type() const override
    {
        static QSGMaterialType materialType;
        return &materialType;
    }

    QSGMaterialShader *createShader(QSGRendererInterface::RenderMode) const override
    {
        return new AccentMaterialShader;
    }

    int compare(const QSGMaterial *other) const override
    {
        const auto *otherMaterial = static_cast<const AccentMaterial *>(other);
        if (const int result = compareFloat(size.width(), otherMaterial->size.width())) {
            return result;
        }
        if (const int result = compareFloat(size.height(), otherMaterial->size.height())) {
            return result;
        }
        if (const int result = compareFloat(radius, otherMaterial->radius)) {
            return result;
        }
        if (const int result = compareFloat(progress, otherMaterial->progress)) {
            return result;
        }
        if (const int result = compareColor(accent, otherMaterial->accent)) {
            return result;
        }
        if (const int result = compareColor(neutral, otherMaterial->neutral)) {
            return result;
        }
        return compareFloat(edgeType, otherMaterial->edgeType);
    }

    QSizeF size;
    qreal radius = 0.0;
    qreal progress = 0.0;
    QColor accent;
    QColor neutral;
    qreal edgeType = 0.0;
};

bool AccentMaterialShader::updateUniformData(RenderState &state, QSGMaterial *newMaterial, QSGMaterial *)
{
    auto *uniformData = state.uniformData();
    if (uniformData->size() != kUniformBlockSize) {
        uniformData->resize(kUniformBlockSize);
    }

    const auto *material = static_cast<AccentMaterial *>(newMaterial);

    writeMatrix(uniformData, 0, state.combinedMatrix());
    writeVector(uniformData, 64, QVector4D(state.opacity(), 0.0f, 0.0f, 0.0f));
    writeVector(uniformData, 80, QVector4D(
        float(material->size.width()),
        float(material->size.height()),
        float(material->radius),
        float(material->progress)));
    writeVector(uniformData, 96, colorVector(material->accent));
    writeVector(uniformData, 112, colorVector(material->neutral));
    writeVector(uniformData, 128, QVector4D(float(material->edgeType), 0.0f, 0.0f, 0.0f));
    return true;
}

class ShimmerMaterialShader final : public QSGMaterialShader
{
public:
    ShimmerMaterialShader()
    {
        setShaderFileName(VertexStage, QStringLiteral(":/coyin/chrome/shaders/surface.vert.qsb"));
        setShaderFileName(FragmentStage, QStringLiteral(":/coyin/chrome/shaders/shimmer_rail.frag.qsb"));
    }

    bool updateUniformData(RenderState &state, QSGMaterial *newMaterial, QSGMaterial *) override;
};

class ShimmerMaterial final : public QSGMaterial
{
public:
    ShimmerMaterial()
    {
        setFlag(Blending, true);
    }

    QSGMaterialType *type() const override
    {
        static QSGMaterialType materialType;
        return &materialType;
    }

    QSGMaterialShader *createShader(QSGRendererInterface::RenderMode) const override
    {
        return new ShimmerMaterialShader;
    }

    int compare(const QSGMaterial *other) const override
    {
        const auto *otherMaterial = static_cast<const ShimmerMaterial *>(other);
        if (const int result = compareFloat(size.width(), otherMaterial->size.width())) {
            return result;
        }
        if (const int result = compareFloat(size.height(), otherMaterial->size.height())) {
            return result;
        }
        if (const int result = compareFloat(radius, otherMaterial->radius)) {
            return result;
        }
        if (const int result = compareFloat(phase, otherMaterial->phase)) {
            return result;
        }
        if (const int result = compareFloat(running ? 1.0 : 0.0, otherMaterial->running ? 1.0 : 0.0)) {
            return result;
        }
        if (const int result = compareColor(accent, otherMaterial->accent)) {
            return result;
        }
        return compareColor(base, otherMaterial->base);
    }

    QSizeF size;
    qreal radius = 0.0;
    qreal phase = 0.0;
    bool running = true;
    QColor accent;
    QColor base;
};

bool ShimmerMaterialShader::updateUniformData(RenderState &state, QSGMaterial *newMaterial, QSGMaterial *)
{
    auto *uniformData = state.uniformData();
    if (uniformData->size() != kUniformBlockSize) {
        uniformData->resize(kUniformBlockSize);
    }

    const auto *material = static_cast<ShimmerMaterial *>(newMaterial);

    writeMatrix(uniformData, 0, state.combinedMatrix());
    writeVector(uniformData, 64, QVector4D(state.opacity(), 0.0f, 0.0f, 0.0f));
    writeVector(uniformData, 80, QVector4D(
        float(material->size.width()),
        float(material->size.height()),
        float(material->radius),
        0.0f));
    writeVector(uniformData, 96, colorVector(material->accent));
    writeVector(uniformData, 112, colorVector(material->base));
    writeVector(uniformData, 128, QVector4D(material->running ? 1.0f : 0.0f, float(material->phase), 0.0f, 0.0f));
    return true;
}

QSGGeometryNode *ensureTexturedQuadNode(QSGNode *oldNode, QSGMaterial *material)
{
    auto *node = static_cast<QSGGeometryNode *>(oldNode);
    if (node) {
        return node;
    }

    node = new QSGGeometryNode;
    auto *geometry = new QSGGeometry(QSGGeometry::defaultAttributes_TexturedPoint2D(), 4);
    geometry->setDrawingMode(QSGGeometry::DrawTriangleStrip);
    geometry->setVertexDataPattern(QSGGeometry::DynamicPattern);
    node->setGeometry(geometry);
    node->setFlag(QSGNode::OwnsGeometry, true);
    node->setMaterial(material);
    node->setFlag(QSGNode::OwnsMaterial, true);
    return node;
}

void updateTexturedNodeGeometry(QSGGeometryNode *node, const QRectF &rect)
{
    QSGGeometry::updateTexturedRectGeometry(node->geometry(), rect, QRectF(0.0, 0.0, 1.0, 1.0));
    node->markDirty(QSGNode::DirtyGeometry);
}

}

SignalAccentItem::SignalAccentItem(QQuickItem *parent)
    : QQuickItem(parent)
{
    setFlag(ItemHasContents, true);
    connect(this, &QQuickItem::windowChanged, this, &SignalAccentItem::onWindowChanged);
    connect(this, &QQuickItem::visibleChanged, this, &SignalAccentItem::onVisibleOrEnabledChanged);
    connect(this, &QQuickItem::enabledChanged, this, &SignalAccentItem::onVisibleOrEnabledChanged);
}

bool SignalAccentItem::active() const
{
    return m_active;
}

void SignalAccentItem::setActive(bool value)
{
    if (m_active == value) {
        return;
    }
    m_active = value;
    emit activeChanged();
    animate();
}

bool SignalAccentItem::hovered() const
{
    return m_hovered;
}

void SignalAccentItem::setHovered(bool value)
{
    if (value && (!isVisible() || !isEnabled())) {
        value = false;
    }
    if (m_hovered == value) {
        return;
    }
    m_hovered = value;
    emit hoveredChanged();
    animate();
}

bool SignalAccentItem::pressed() const
{
    return m_pressed;
}

void SignalAccentItem::setPressed(bool value)
{
    if (value && (!isVisible() || !isEnabled())) {
        value = false;
    }
    if (m_pressed == value) {
        return;
    }
    m_pressed = value;
    emit pressedChanged();
    animate();
}

QColor SignalAccentItem::accentColor() const
{
    return m_accent;
}

void SignalAccentItem::setAccentColor(const QColor &value)
{
    const QColor color(value);
    if (m_accent == color) {
        return;
    }
    m_accent = color;
    emit accentColorChanged();
    update();
}

QColor SignalAccentItem::neutralColor() const
{
    return m_neutral;
}

void SignalAccentItem::setNeutralColor(const QColor &value)
{
    const QColor color(value);
    if (m_neutral == color) {
        return;
    }
    m_neutral = color;
    emit neutralColorChanged();
    update();
}

QString SignalAccentItem::edge() const
{
    return m_edge;
}

void SignalAccentItem::setEdge(const QString &value)
{
    if (m_edge == value) {
        return;
    }
    m_edge = value;
    emit edgeChanged();
    update();
}

qreal SignalAccentItem::radius() const
{
    return m_radius;
}

void SignalAccentItem::setRadius(qreal value)
{
    if (qAbs(m_radius - value) < 0.01) {
        return;
    }
    m_radius = value;
    emit radiusChanged();
    update();
}

void SignalAccentItem::tickAnimation()
{
    if (!m_clock.isValid()) {
        m_timer.stop();
        return;
    }

    const qreal progress = qMin<qreal>(1.0, m_clock.elapsed() / qreal(m_durationMs));
    const qreal eased = m_curve.valueForProgress(progress);
    m_progress = m_fromProgress + (m_toProgress - m_fromProgress) * eased;
    update();

    if (progress >= 1.0) {
        SharedAnimationDriver::instance().deactivate(this);
        m_progress = m_toProgress;
        update();
    }
}

void SignalAccentItem::onWindowChanged(QQuickWindow *window)
{
    if (m_window == window) {
        return;
    }
    if (m_window) {
        disconnect(m_window.data(), &QWindow::activeChanged, this, &SignalAccentItem::onWindowActiveChanged);
    }
    m_window = window;
    if (m_window) {
        connect(m_window.data(), &QWindow::activeChanged, this, &SignalAccentItem::onWindowActiveChanged);
    }
}

void SignalAccentItem::onWindowActiveChanged()
{
    if (window() && !window()->isActive()) {
        clearInteraction();
    }
}

void SignalAccentItem::onVisibleOrEnabledChanged()
{
    if (!isVisible() || !isEnabled()) {
        clearInteraction();
    }
}

qreal SignalAccentItem::targetProgress() const
{
    if (m_pressed) {
        return 1.0;
    }
    if (m_active) {
        return 0.92;
    }
    if (m_hovered) {
        return 0.58;
    }
    return 0.0;
}

void SignalAccentItem::animate()
{
    if (!isVisible() || !isEnabled()) {
        clearInteraction();
        return;
    }

    const qreal target = targetProgress();
    if (qAbs(target - m_progress) < 0.001) {
        m_progress = target;
        update();
        return;
    }

    m_fromProgress = m_progress;
    m_toProgress = target;
    m_clock.restart();
    SharedAnimationDriver::instance().activate(this, &SignalAccentItem::tickAnimation);
}

void SignalAccentItem::clearInteraction()
{
    m_hovered = false;
    m_pressed = false;
    if (!m_active) {
        m_progress = 0.0;
    }
    SharedAnimationDriver::instance().deactivate(this);
    update();
}

QSGNode *SignalAccentItem::updatePaintNode(QSGNode *oldNode, UpdatePaintNodeData *)
{
    auto *node = ensureTexturedQuadNode(oldNode, new AccentMaterial);
    updateTexturedNodeGeometry(node, boundingRect());

    auto *material = static_cast<AccentMaterial *>(node->material());
    material->size = QSizeF(width(), height());
    material->radius = m_radius;
    material->progress = m_progress;
    material->accent = m_accent;
    material->neutral = m_neutral;
    material->edgeType = edgeTypeForString(m_edge);
    node->markDirty(QSGNode::DirtyMaterial);
    return node;
}

void SignalAccentItem::geometryChange(const QRectF &newGeometry, const QRectF &oldGeometry)
{
    QQuickItem::geometryChange(newGeometry, oldGeometry);
    if (newGeometry != oldGeometry) {
        update();
    }
}

void SignalAccentItem::itemChange(ItemChange change, const ItemChangeData &value)
{
    QQuickItem::itemChange(change, value);
    if ((change == ItemVisibleHasChanged || change == ItemEnabledHasChanged) && (!isVisible() || !isEnabled())) {
        clearInteraction();
    }
}

ShimmerRailItem::ShimmerRailItem(QQuickItem *parent)
    : QQuickItem(parent)
{
    setFlag(ItemHasContents, true);
    connect(this, &QQuickItem::visibleChanged, this, &ShimmerRailItem::updateTimerState);
    connect(this, &QQuickItem::enabledChanged, this, &ShimmerRailItem::updateTimerState);
    updateTimerState();
}

bool ShimmerRailItem::running() const
{
    return m_running;
}

void ShimmerRailItem::setRunning(bool value)
{
    if (m_running == value) {
        return;
    }
    m_running = value;
    updateTimerState();
    emit runningChanged();
    update();
}

QColor ShimmerRailItem::accentColor() const
{
    return m_accent;
}

void ShimmerRailItem::setAccentColor(const QColor &value)
{
    const QColor color(value);
    if (m_accent == color) {
        return;
    }
    m_accent = color;
    emit accentColorChanged();
    update();
}

QColor ShimmerRailItem::baseColor() const
{
    return m_base;
}

void ShimmerRailItem::setBaseColor(const QColor &value)
{
    const QColor color(value);
    if (m_base == color) {
        return;
    }
    m_base = color;
    emit baseColorChanged();
    update();
}

qreal ShimmerRailItem::radius() const
{
    return m_radius;
}

void ShimmerRailItem::setRadius(qreal value)
{
    if (qAbs(m_radius - value) < 0.01) {
        return;
    }
    m_radius = value;
    emit radiusChanged();
    update();
}

void ShimmerRailItem::tick()
{
    if (!m_running) {
        return;
    }
    m_phase = std::fmod(m_phase + 0.035, 1.0);
    update();
}

void ShimmerRailItem::updateTimerState()
{
    const bool shouldRun = m_running && isVisible() && isEnabled();
    if (shouldRun) {
        SharedAnimationDriver::instance().activate(this, &ShimmerRailItem::tick);
    } else {
        SharedAnimationDriver::instance().deactivate(this);
    }
}

QSGNode *ShimmerRailItem::updatePaintNode(QSGNode *oldNode, UpdatePaintNodeData *)
{
    auto *node = ensureTexturedQuadNode(oldNode, new ShimmerMaterial);
    updateTexturedNodeGeometry(node, boundingRect());

    auto *material = static_cast<ShimmerMaterial *>(node->material());
    material->size = QSizeF(width(), height());
    material->radius = m_radius;
    material->phase = m_phase;
    material->running = m_running;
    material->accent = m_accent;
    material->base = m_base;
    node->markDirty(QSGNode::DirtyMaterial);
    return node;
}

void ShimmerRailItem::geometryChange(const QRectF &newGeometry, const QRectF &oldGeometry)
{
    QQuickItem::geometryChange(newGeometry, oldGeometry);
    if (newGeometry != oldGeometry) {
        update();
    }
}

InteractionStateItem::InteractionStateItem(QQuickItem *parent)
    : QQuickItem(parent)
{
    connect(this, &QQuickItem::windowChanged, this, &InteractionStateItem::onWindowChanged);
}

QString InteractionStateItem::resolvedState() const
{
    return m_resolvedState;
}

bool InteractionStateItem::active() const
{
    return m_resolvedState == QLatin1String("pressed")
        || m_resolvedState == QLatin1String("busy")
        || m_resolvedState == QLatin1String("selected")
        || m_resolvedState == QLatin1String("focused");
}

bool InteractionStateItem::hovered() const
{
    return m_resolvedState == QLatin1String("hover");
}

bool InteractionStateItem::pressed() const
{
    return m_resolvedState == QLatin1String("pressed");
}

bool InteractionStateItem::focused() const
{
    return m_resolvedState == QLatin1String("focused");
}

qreal InteractionStateItem::hoverProgress() const
{
    return m_hoverProgress;
}

qreal InteractionStateItem::pressProgress() const
{
    return m_pressProgress;
}

qreal InteractionStateItem::focusProgress() const
{
    return m_focusProgress;
}

qreal InteractionStateItem::selectionProgress() const
{
    return m_selectionProgress;
}

qreal InteractionStateItem::busyProgress() const
{
    return m_busyProgress;
}

qreal InteractionStateItem::engageProgress() const
{
    return m_engageProgress;
}

qreal InteractionStateItem::accentStrength() const
{
    return qBound<qreal>(
        0.0,
        m_hoverProgress * 0.22
            + m_focusProgress * 0.34
            + m_pressProgress * 0.54
            + m_selectionProgress * 0.40
            + m_busyProgress * 0.46,
        1.0);
}

qreal InteractionStateItem::frameStrength() const
{
    return qBound<qreal>(
        0.0,
        m_hoverProgress * 0.16
            + m_focusProgress * 0.32
            + m_pressProgress * 0.42
            + m_selectionProgress * 0.24
            + m_busyProgress * 0.28,
        1.0);
}

qreal InteractionStateItem::textStrength() const
{
    return qBound<qreal>(
        0.0,
        m_hoverProgress * 0.16
            + m_focusProgress * 0.24
            + m_pressProgress * 0.12
            + m_selectionProgress * 0.18
            + m_busyProgress * 0.14,
        1.0);
}

qreal InteractionStateItem::settleStrength() const
{
    return qMax(
        qMax(m_focusProgress * 0.82, m_selectionProgress * 0.92),
        m_busyProgress * 0.95);
}

bool InteractionStateItem::enabledInput() const
{
    return m_enabledInput;
}

void InteractionStateItem::setEnabledInput(bool value)
{
    if (m_enabledInput == value) {
        return;
    }
    m_enabledInput = value;
    emit enabledInputChanged();
    updateState();
}

bool InteractionStateItem::visibleInput() const
{
    return m_visibleInput;
}

void InteractionStateItem::setVisibleInput(bool value)
{
    if (m_visibleInput == value) {
        return;
    }
    m_visibleInput = value;
    emit visibleInputChanged();
    updateState();
}

bool InteractionStateItem::hoveredInput() const
{
    return m_hoveredInput;
}

void InteractionStateItem::setHoveredInput(bool value)
{
    if (m_hoveredInput == value) {
        return;
    }
    m_hoveredInput = value;
    emit hoveredInputChanged();
    updateState();
}

bool InteractionStateItem::pressedInput() const
{
    return m_pressedInput;
}

void InteractionStateItem::setPressedInput(bool value)
{
    if (m_pressedInput == value) {
        return;
    }
    m_pressedInput = value;
    emit pressedInputChanged();
    updateState();
}

bool InteractionStateItem::focusedInput() const
{
    return m_focusedInput;
}

void InteractionStateItem::setFocusedInput(bool value)
{
    if (m_focusedInput == value) {
        return;
    }
    m_focusedInput = value;
    emit focusedInputChanged();
    updateState();
}

bool InteractionStateItem::busyInput() const
{
    return m_busyInput;
}

void InteractionStateItem::setBusyInput(bool value)
{
    if (m_busyInput == value) {
        return;
    }
    m_busyInput = value;
    emit busyInputChanged();
    updateState();
}

bool InteractionStateItem::selectedInput() const
{
    return m_selectedInput;
}

void InteractionStateItem::setSelectedInput(bool value)
{
    if (m_selectedInput == value) {
        return;
    }
    m_selectedInput = value;
    emit selectedInputChanged();
    updateState();
}

void InteractionStateItem::onWindowChanged(QQuickWindow *window)
{
    if (m_window == window) {
        return;
    }
    if (m_window) {
        disconnect(m_window.data(), &QWindow::activeChanged, this, &InteractionStateItem::updateState);
    }
    m_window = window;
    if (m_window) {
        connect(m_window.data(), &QWindow::activeChanged, this, &InteractionStateItem::updateState);
    }
    updateState();
}

void InteractionStateItem::updateState()
{
    bool clearedHover = false;
    bool clearedPress = false;
    if (!m_visibleInput || !windowActive()) {
        if (m_hoveredInput) {
            m_hoveredInput = false;
            clearedHover = true;
        }
        if (m_pressedInput) {
            m_pressedInput = false;
            clearedPress = true;
        }
    }

    if (clearedHover) {
        emit hoveredInputChanged();
    }
    if (clearedPress) {
        emit pressedInputChanged();
    }

    const QString nextState = computeState();
    if (nextState != m_resolvedState) {
        m_resolvedState = nextState;
        emit resolvedStateChanged();
        emit hoveredChanged();
        emit pressedChanged();
        emit focusedChanged();
        emit activeChanged();
    }

    animateProgresses();
}

bool InteractionStateItem::windowActive() const
{
    return !m_window || m_window->isActive();
}

QString InteractionStateItem::computeState() const
{
    if (!m_enabledInput) {
        return QStringLiteral("disabled");
    }
    if (!m_visibleInput || !windowActive()) {
        return QStringLiteral("normal");
    }
    if (m_pressedInput) {
        return QStringLiteral("pressed");
    }
    if (m_busyInput) {
        return QStringLiteral("busy");
    }
    if (m_selectedInput) {
        return QStringLiteral("selected");
    }
    if (m_focusedInput) {
        return QStringLiteral("focused");
    }
    if (m_hoveredInput) {
        return QStringLiteral("hover");
    }
    return QStringLiteral("normal");
}

void InteractionStateItem::animateProgresses()
{
    const bool interactive = m_enabledInput && m_visibleInput && windowActive();
    const qreal hoverTarget = interactive && m_hoveredInput ? 1.0 : 0.0;
    const qreal pressTarget = interactive && m_pressedInput ? 1.0 : 0.0;
    const qreal focusTarget = interactive && m_focusedInput ? 1.0 : 0.0;
    const qreal selectionTarget = interactive && m_selectedInput ? 1.0 : 0.0;
    const qreal busyTarget = interactive && m_busyInput ? 1.0 : 0.0;
    const qreal engageTarget = std::max(
        std::max(hoverTarget * 0.62, focusTarget * 0.78),
        std::max(pressTarget, std::max(selectionTarget * 0.86, busyTarget * 0.90)));

    const bool changed =
        qAbs(m_hoverTo - hoverTarget) > 0.0001
        || qAbs(m_pressTo - pressTarget) > 0.0001
        || qAbs(m_focusTo - focusTarget) > 0.0001
        || qAbs(m_selectionTo - selectionTarget) > 0.0001
        || qAbs(m_busyTo - busyTarget) > 0.0001
        || qAbs(m_engageTo - engageTarget) > 0.0001;

    if (!changed) {
        return;
    }

    m_hoverFrom = m_hoverProgress;
    m_hoverTo = hoverTarget;
    m_pressFrom = m_pressProgress;
    m_pressTo = pressTarget;
    m_focusFrom = m_focusProgress;
    m_focusTo = focusTarget;
    m_selectionFrom = m_selectionProgress;
    m_selectionTo = selectionTarget;
    m_busyFrom = m_busyProgress;
    m_busyTo = busyTarget;
    m_engageFrom = m_engageProgress;
    m_engageTo = engageTarget;
    m_animationClock.restart();
    SharedAnimationDriver::instance().activate(this, &InteractionStateItem::tickAnimation);
}

void InteractionStateItem::tickAnimation()
{
    if (!m_animationClock.isValid()) {
        SharedAnimationDriver::instance().deactivate(this);
        return;
    }

    const qreal progress = qMin<qreal>(1.0, m_animationClock.elapsed() / qreal(m_animationDurationMs));
    const qreal eased = m_animationCurve.valueForProgress(progress);

    const auto updateChannel = [eased](qreal from, qreal to, qreal &current, auto signal) {
        const qreal next = from + (to - from) * eased;
        if (qAbs(next - current) > 0.0001) {
            current = next;
            signal();
        }
    };

    updateChannel(m_hoverFrom, m_hoverTo, m_hoverProgress, [this]() { emit hoverProgressChanged(); });
    updateChannel(m_pressFrom, m_pressTo, m_pressProgress, [this]() { emit pressProgressChanged(); });
    updateChannel(m_focusFrom, m_focusTo, m_focusProgress, [this]() { emit focusProgressChanged(); });
    updateChannel(m_selectionFrom, m_selectionTo, m_selectionProgress, [this]() { emit selectionProgressChanged(); });
    updateChannel(m_busyFrom, m_busyTo, m_busyProgress, [this]() { emit busyProgressChanged(); });
    updateChannel(m_engageFrom, m_engageTo, m_engageProgress, [this]() { emit engageProgressChanged(); });
    emit visualProgressChanged();

    if (progress >= 1.0) {
        SharedAnimationDriver::instance().deactivate(this);
        if (qAbs(m_hoverProgress - m_hoverTo) > 0.0001) {
            m_hoverProgress = m_hoverTo;
            emit hoverProgressChanged();
        }
        if (qAbs(m_pressProgress - m_pressTo) > 0.0001) {
            m_pressProgress = m_pressTo;
            emit pressProgressChanged();
        }
        if (qAbs(m_focusProgress - m_focusTo) > 0.0001) {
            m_focusProgress = m_focusTo;
            emit focusProgressChanged();
        }
        if (qAbs(m_selectionProgress - m_selectionTo) > 0.0001) {
            m_selectionProgress = m_selectionTo;
            emit selectionProgressChanged();
        }
        if (qAbs(m_busyProgress - m_busyTo) > 0.0001) {
            m_busyProgress = m_busyTo;
            emit busyProgressChanged();
        }
        if (qAbs(m_engageProgress - m_engageTo) > 0.0001) {
            m_engageProgress = m_engageTo;
            emit engageProgressChanged();
        }
        emit visualProgressChanged();
    }
}

DisclosureMotionItem::DisclosureMotionItem(QQuickItem *parent)
    : QQuickItem(parent)
{
}

bool DisclosureMotionItem::expanded() const
{
    return m_expanded;
}

void DisclosureMotionItem::setExpanded(bool value)
{
    if (m_expanded == value) {
        return;
    }
    m_expanded = value;
    emit expandedChanged();
    animate();
}

qreal DisclosureMotionItem::progress() const
{
    return m_progress;
}

int DisclosureMotionItem::duration() const
{
    return m_durationMs;
}

void DisclosureMotionItem::setDuration(int value)
{
    const int normalized = qMax(60, value);
    if (m_durationMs == normalized) {
        return;
    }
    m_durationMs = normalized;
    emit durationChanged();
}

void DisclosureMotionItem::tick()
{
    if (!m_clock.isValid()) {
        SharedAnimationDriver::instance().deactivate(this);
        return;
    }

    const qreal progressValue = qMin<qreal>(1.0, m_clock.elapsed() / qreal(m_durationMs));
    const qreal eased = m_curve.valueForProgress(progressValue);
    const qreal nextValue = m_fromProgress + (m_toProgress - m_fromProgress) * eased;
    if (qAbs(nextValue - m_progress) > 0.0001) {
        m_progress = nextValue;
        emit progressChanged();
    }

    if (progressValue >= 1.0) {
        SharedAnimationDriver::instance().deactivate(this);
        if (qAbs(m_progress - m_toProgress) > 0.0001) {
            m_progress = m_toProgress;
            emit progressChanged();
        }
    }
}

void DisclosureMotionItem::animate()
{
    const qreal target = m_expanded ? 1.0 : 0.0;
    if (qAbs(target - m_progress) < 0.0001) {
        if (qAbs(m_progress - target) > 0.0) {
            m_progress = target;
            emit progressChanged();
        }
        return;
    }

    m_fromProgress = m_progress;
    m_toProgress = target;
    m_clock.restart();
    SharedAnimationDriver::instance().activate(this, &DisclosureMotionItem::tick);
}

extern "C" __declspec(dllexport) int coyin_register_qml_types()
{
    static bool registered = false;
    if (registered) {
        return 1;
    }

    qmlRegisterType<SignalAccentItem>("Coyin.Chrome", 1, 0, "SignalAccent");
    qmlRegisterType<ShimmerRailItem>("Coyin.Chrome", 1, 0, "ShimmerRail");
    qmlRegisterType<InteractionStateItem>("Coyin.Chrome", 1, 0, "InteractionState");
    qmlRegisterType<DisclosureMotionItem>("Coyin.Chrome", 1, 0, "DisclosureMotion");

    registered = true;
    return 1;
}
