```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>摆线齿轮 - 54齿</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0a0e17;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    font-family: 'Segoe UI', sans-serif;
    color: #c0d0e0;
    overflow: hidden;
  }
  h1 {
    font-size: 1.6rem;
    margin-bottom: 10px;
    background: linear-gradient(90deg, #4fc3f7, #ab47bc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 2px;
  }
  .info {
    font-size: 0.85rem;
    color: #607080;
    margin-bottom: 16px;
    text-align: center;
    line-height: 1.6;
  }
  #gear-container {
    position: relative;
    width: 700px;
    height: 700px;
  }
  svg {
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 0 20px rgba(79,195,247,0.15));
  }
  .controls {
    margin-top: 16px;
    display: flex;
    gap: 12px;
    align-items: center;
  }
  button {
    background: linear-gradient(135deg, #1a2a3a, #2a3a4a);
    color: #4fc3f7;
    border: 1px solid #2a4a5a;
    padding: 8px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.3s;
  }
  button:hover {
    background: linear-gradient(135deg, #2a3a4a, #3a5a6a);
    border-color: #4fc3f7;
    box-shadow: 0 0 12px rgba(79,195,247,0.3);
  }
  .speed-label { font-size: 0.8rem; color: #506070; }
</style>
</head>
<body>

<h1>⚙ 摆线齿轮 Cycloidal Gear</h1>
<div class="info">
  齿数: 54 &nbsp;|&nbsp; 齿形: 摆线 (Cycloidal) &nbsp;|&nbsp; 外摆线齿顶 + 内摆线齿根
</div>

<div id="gear-container">
  <svg id="gearSvg" viewBox="0 0 700 700"></svg>
</div>

<div class="controls">
  <button onclick="toggleRotation()">⏯ 旋转 / 暂停</button>
  <button onclick="toggleFill()">◐ 填充切换</button>
  <span class="speed-label">速度:</span>
  <button onclick="changeSpeed(-0.5)">−</button>
  <button onclick="changeSpeed(0.5)">+</button>
</div>

<script>
const SVG_NS = "http://www.w3.org/2000/svg";
const svg = document.getElementById("gearSvg");

// ── 齿轮参数 ──
const NUM_TEETH = 54;
const PITCH_RADIUS = 220;
const ADDENDUM_GEN_RADIUS = 38;   // 外摆线生成圆半径 (齿顶)
const DEDENDUM_GEN_RADIUS = 38;   // 内摆线生成圆半径 (齿根)
const ADDENDUM_HEIGHT = 18;
const DEDENDUM_DEPTH = 14;
const TOOTH_WIDTH_RATIO = 0.48;   // 齿宽占齿距的比例
const HOLE_RADIUS = 30;
const SPOKE_COUNT = 6;
const SPOKE_WIDTH = 14;
const RIM_WIDTH = 22;

const CX = 350, CY = 350;

let rotationAngle = 0;
let rotating = true;
let speed = 1;
let showFill = true;
let animId;

// ── 数学工具 ──
function deg2rad(d) { return d * Math.PI / 180; }

// 外摆线 (Epicycloid) — 齿顶部分
// 基圆 = 节圆, 滚动圆在外部滚动
function epicycloidPoint(R, r, theta) {
  const x = (R + r) * Math.cos(theta) - r * Math.cos((R + r) / r * theta);
  const y = (R + r) * Math.sin(theta) - r * Math.sin((R + r) / r * theta);
  return [x, y];
}

// 内摆线 (Hypocycloid) — 齿根部分
// 基圆 = 节圆, 滚动圆在内部滚动
function hypocycloidPoint(R, r, theta) {
  const x = (R - r) * Math.cos(theta) + r * Math.cos((R - r) / r * theta);
  const y = (R - r) * Math.sin(theta) - r * Math.sin((R - r) / r * theta);
  return [x, y];
}

// ── 生成单个齿的轮廓点 ──
function generateToothProfile(toothIndex) {
  const toothAngle = (360 / NUM_TEETH) * toothIndex;
  const halfToothAngle = (360 / NUM_TEETH) * TOOTH_WIDTH_RATIO / 2;
  const points = [];

  // 齿顶: 外摆线 (左右两侧)
  const epSteps = 12;
  const epMaxAngle = deg2rad(halfToothAngle * 1.8);

  // 右侧齿顶 (外摆线)
  for (let i = 0; i <= epSteps; i++) {
    const t = (i / epSteps) * epMaxAngle;
    const [ex, ey] = epicycloidPoint(PITCH_RADIUS, ADDENDUM_GEN_RADIUS, t);
    const angle = Math.atan2(ey, ex);
    const dist = Math.sqrt(ex * ex + ey * ey);
    const targetDist = PITCH_RADIUS + ADDENDUM_HEIGHT * (i / epSteps);
    const scale = targetDist / dist;
    points.push({
      x: CX + ex * scale * Math.cos(deg2rad(toothAngle)) - ey * scale * Math.sin(deg2rad(toothAngle)),
      y: CY + ex * scale * Math.sin(deg2rad(toothAngle)) + ey * scale * Math.cos(deg2rad(toothAngle))
    });
  }

  // 齿顶圆弧
  const topArcSteps = 6;
  const topStartAngle = deg2rad(toothAngle + halfToothAngle * 0.6);
  const topEndAngle = deg2rad(toothAngle - halfToothAngle * 0.6);
  const topRadius = PITCH_RADIUS + ADDENDUM_HEIGHT;
  for (let i = 0; i <= topArcSteps; i++) {
    const a = topStartAngle + (topEndAngle - topStartAngle) * (i / topArcSteps);
    points.push({
      x: CX + topRadius * Math.cos(a),
      y: CY + topRadius * Math.sin(a)
    });
  }

  // 左侧齿顶 (外摆线, 镜像)
  for (let i = epSteps; i >= 0; i--) {
    const t = (i / epSteps) * epMaxAngle;
    const [ex, ey] = epicycloidPoint(PITCH_RADIUS, ADDENDUM_GEN_RADIUS, -t);
    const dist = Math.sqrt(ex * ex + ey * ey);
    const targetDist = PITCH_RADIUS + ADDENDUM_HEIGHT * (i / epSteps);
    const scale = targetDist / dist;
    points.push({
      x: CX + ex * scale * Math.cos(deg2rad(toothAngle)) - ey * scale * Math.sin(deg2rad(toothAngle)),
      y: CY + ex * scale * Math.sin(deg2rad(toothAngle)) + ey * scale * Math.cos(deg2rad(toothAngle))
    });
  }

  return points;
}

// ── 生成完整齿轮轮廓 ──
function generateGearPath() {
  const allPoints = [];
  const toothPitchAngle = 360 / NUM_TEETH;

  for (let t = 0; t < NUM_TEETH; t++) {
    const toothCenterAngle = t * toothPitchAngle;
    const halfPitch = toothPitchAngle / 2;

    // 齿根圆弧 (齿间)
    const rootStartAngle = deg2rad(toothCenterAngle + halfPitch * TOOTH_WIDTH_RATIO + halfPitch * (1 - TOOTH_WIDTH_RATIO) * 0.3);
    const rootEndAngle = deg2rad(toothCenterAngle + halfPitch * TOOTH_WIDTH_RATIO + halfPitch * (1 - TOOTH_WIDTH_RATIO) * 0.7);
    const rootRadius = PITCH_RADIUS - DEDENDUM_DEPTH;

    // 齿根过渡
    const rootSteps = 8;
    for (let i = 0; i <= rootSteps; i++) {
      const a = rootStartAngle + (rootEndAngle - rootStartAngle) * (i / rootSteps);
      allPoints.push({
        x: CX + rootRadius * Math.cos(a),
        y: CY + rootRadius * Math.sin(a)
      });
    }

    // 齿根到齿侧的过渡 (内摆线)
    const hypSteps = 10;
    const hypMaxAngle = deg2rad(halfPitch * TOOTH_WIDTH_RATIO * 0.9);
    for (let i = 0; i <= hypSteps; i++) {
      const frac = i / hypSteps;
      const ht = frac * hypMaxAngle;
      const [hx, hy] = hypocycloidPoint(PITCH_RADIUS, DEDENDUM_GEN_RADIUS, ht);
      const dist = Math.sqrt(hx * hx + hy * hy);
      const targetDist = rootRadius + (PITCH_RADIUS - rootRadius) * frac;
      const scale = targetDist / dist;
      const angle = toothCenterAngle + halfPitch * TOOTH_WIDTH_RATIO * 0.5;
      allPoints.push({
        x: CX + hx * scale * Math.cos(deg2rad(angle)) - hy * scale * Math.sin(deg2rad(angle)),
        y: CY + hx * scale * Math.sin(deg2rad(angle)) + hy * scale * Math.cos(deg2rad(angle))
      });
    }

    // 齿顶 (外摆线)
    const epSteps = 14;
    const epMaxAngle = deg2rad(halfPitch * TOOTH_WIDTH_RATIO * 1.2);
    for (let i = 0; i <= epSteps; i++) {
      const frac = i / epSteps;
      const et = -epMaxAngle + 2 * epMaxAngle * frac;
      const [ex, ey] = epicycloidPoint(PITCH_RADIUS, ADDENDUM_GEN_RADIUS, et);
      const dist = Math.sqrt(ex * ex + ey * ey);
      const targetDist = PITCH_RADIUS + ADDENDUM_HEIGHT * Math.cos((frac - 0.5) * Math.PI);
      const scale = targetDist / dist;
      allPoints.push({
        x: CX + ex * scale * Math.cos(deg2rad(toothCenterAngle)) - ey * scale * Math.sin(deg2rad(toothCenterAngle)),
        y: CY + ex * scale * Math.sin(deg2rad(toothCenterAngle)) + ey * scale * Math.cos(deg2rad(toothCenterAngle))
      });
    }

    // 齿侧回到齿根 (内摆线)
    for (let i = hypSteps; i >= 0; i--) {
      const frac = i / hypSteps;
      const ht = frac * hypMaxAngle;
      const [hx, hy] = hypocycloidPoint(PITCH_RADIUS, DEDENDUM_GEN_RADIUS, -ht);
      const dist = Math.sqrt(hx * hx + hy * hy);
      const targetDist = rootRadius + (PITCH_RADIUS - rootRadius) * frac;
      const scale = targetDist / dist;
      const angle = toothCenterAngle - halfPitch * TOOTH_WIDTH_RATIO * 0.5;
      allPoints.push({
        x: CX + hx * scale * Math.cos(deg2rad(angle)) - hy * scale * Math.sin(deg2rad(angle)),
        y: CY + hx * scale * Math.sin(deg2rad(angle)) + hy * scale * Math.cos(deg2rad(angle))
      });
    }
  }

  return allPoints;
}

// ── 构建 SVG 路径 ──
function buildPathD(points) {
  if (points.length === 0) return "";
  let d = `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`;
  for (let i = 1; i < points.length; i++) {
    d += ` L ${points[i].x.toFixed(2)} ${points[i].y.toFixed(2)}`;
  }
  d += " Z";
  return d;
}

// ── 生成轮辐和轮毂 ──
function generateSpokes() {
  const innerRimR = PITCH_RADIUS - DEDENDUM_DEPTH - RIM_WIDTH;
  const hubR = HOLE_RADIUS + 18;
  const paths = [];

  for (let i = 0; i < SPOKE_COUNT; i++) {
    const angle = deg2rad((360 / SPOKE_COUNT) * i);
    const halfW = deg2rad(SPOKE_WIDTH / innerRimR * (180 / Math.PI) * 0.5);

    const x1i = CX + hubR * Math.cos(angle - halfW);
    const y1i = CY + hubR * Math.sin(angle - halfW);
    const x2i = CX + hubR * Math.cos(angle + halfW);
    const y2i = CY + hubR * Math.sin(angle + halfW);
    const x1o = CX + innerRimR * Math.cos(angle - halfW * 0.7);
    const y1o = CY + innerRimR * Math.sin(angle - halfW * 0.7);
    const x2o = CX + innerRimR * Math.cos(angle + halfW * 0.7);
    const y2o = CY + innerRimR * Math.sin(angle + halfW * 0.7);

    paths.push(`M ${x1i} ${y1i} L ${x1o} ${y1o} L ${x2o} ${y2o} L ${x2i} ${y2i} Z`);
  }

  return paths;
}

// ── 渲染齿轮 ──
function renderGear() {
  svg.innerHTML = "";

  // 定义渐变
  const defs = document.createElementNS(SVG_NS, "defs");

  const grad = document.createElementNS(SVG_NS, "linearGradient");
  grad.id = "gearGrad";
  grad.setAttribute("x1", "0%"); grad.setAttribute("y1", "0%");
  grad.setAttribute("x2", "100%"); grad.setAttribute("y2", "100%");
  const s1 = document.createElementNS(SVG_NS, "stop");
  s1.setAttribute("offset", "0%"); s1.setAttribute("stop-color", "#3a7ca5");
  const s2 = document.createElementNS(SVG_NS, "stop");
  s2.setAttribute("offset", "50%"); s2.setAttribute("stop-color", "#5ba3c9");
  const s3 = document.createElementNS(SVG_NS, "stop");
  s3.setAttribute("offset", "100%"); s3.setAttribute("stop-color", "#2a5a7a");
  grad.appendChild(s1); grad.appendChild(s2); grad.appendChild(s3);
  defs.appendChild(grad);

  const grad2 = document.createElementNS(SVG_NS, "radialGradient");
  grad2.id = "holeGrad";
  grad2.setAttribute("cx", "50%"); grad2.setAttribute("cy", "50%");
  grad2.setAttribute("r", "50%");
  const hs1 = document.createElementNS(SVG_NS, "stop");
  hs1.setAttribute("offset", "0%"); hs1.setAttribute("stop-color", "#0a0e17");
  const hs2 = document.createElementNS(SVG_NS, "stop");
  hs2.setAttribute("offset", "100%"); hs2.setAttribute("stop-color", "#1a2a3a");
  grad2.appendChild(hs1); grad2.appendChild(hs2);
  defs.appendChild(grad2);

  // 发光滤镜
  const filter = document.createElementNS(SVG_NS, "filter");
  filter.id = "glow";
  const blur = document.createElementNS(SVG_NS, "feGaussianBlur");
  blur.setAttribute("stdDeviation", "3");
  blur.setAttribute("result", "coloredBlur");
  filter.appendChild(blur);
  const merge = document.createElementNS(SVG_NS, "feMerge");
  const mn1 = document.createElementNS(SVG_NS, "feMergeNode");
  mn1.setAttribute("in", "coloredBlur");
  merge.appendChild(mn1);
  const mn2 = document.createElementNS(SVG_NS, "feMergeNode");
  mn2.setAttribute("in", "SourceGraphic");
  merge.appendChild(mn2);
  filter.appendChild(merge);
  defs.appendChild(filter);

  svg.appendChild(defs);

  // 齿轮组
  const gearGroup = document.createElementNS(SVG_NS, "g");
  gearGroup.setAttribute("transform", `rotate(${rotationAngle}, ${CX}, ${CY})`);
  gearGroup.setAttribute("filter", "url(#glow)");

  const gearPoints = generateGearPath();
  const gearD = buildPathD(gearPoints);

  // 齿轮主体
  const gearPath = document.createElementNS(SVG_NS, "path");
  gearPath.setAttribute("d", gearD);
  gearPath.setAttribute("fill", showFill ? "url(#gearGrad)" : "none");
  gearPath.setAttribute("stroke", "#4fc3f7");
  gearPath.setAttribute("stroke-width", "1.2");
  gearPath.setAttribute("stroke-linejoin", "round");
  gearGroup.appendChild(gearPath);

  // 内圈
  const innerRimR = PITCH_RADIUS - DEDENDUM_DEPTH - RIM_WIDTH;
  const innerCircle = document.createElementNS(SVG_NS, "circle");
  innerCircle.setAttribute("cx", CX);
  innerCircle.setAttribute("cy", CY);
  innerCircle.setAttribute("r", innerRimR);
  innerCircle.setAttribute("fill", "none");
  innerCircle.setAttribute("stroke", "#4fc3f7");
  innerCircle.setAttribute("stroke-width", "0.8");
  innerCircle.setAttribute("opacity", "0.4");
  gearGroup.appendChild(innerCircle);

  // 节圆 (虚线)
  const pitchCircle = document.createElementNS(SVG_NS, "circle");
  pitchCircle.setAttribute("cx", CX);
  pitchCircle.setAttribute("cy", CY);
  pitchCircle.setAttribute("r", PITCH_RADIUS);
  pitchCircle.setAttribute("fill", "none");
  pitchCircle.setAttribute("stroke", "#ab47bc");
  pitchCircle.setAttribute("stroke-width", "0.6");
  pitchCircle.setAttribute("stroke-dasharray", "4,4");
  pitchCircle.setAttribute("opacity", "0.5");
  gearGroup.appendChild(pitchCircle);

  // 轮辐
  const spokePaths = generateSpokes();
  spokePaths.forEach(d => {
    const sp = document.createElementNS(SVG_NS, "path");
    sp.setAttribute("d", d);
    sp.setAttribute("fill", showFill ? "url(#gearGrad)" : "none");
    sp.setAttribute("stroke", "#4fc3f7");
    sp.setAttribute("stroke-width", "1");
    gearGroup.appendChild(sp);
  });

  // 轮毂
  const hubR = HOLE_RADIUS + 18;
  const hubOuter = document.createElementNS(SVG_NS, "circle");
  hubOuter.setAttribute("cx", CX);
  hubOuter.setAttribute("cy", CY);
  hubOuter.setAttribute("r", hubR);
  hubOuter.setAttribute("fill", showFill ? "url(#gearGrad)" : "none");
  hubOuter.setAttribute("stroke", "#4fc3f7");
  hubOuter.setAttribute("stroke-width", "1.2");
  gearGroup.appendChild(hubOuter);

  // 中心孔
  const hole = document.createElementNS(SVG_NS, "circle");
  hole.setAttribute("cx", CX);
  hole.setAttribute("cy", CY);
  hole.setAttribute("r", HOLE_RADIUS);
  hole.setAttribute("fill", "url(#holeGrad)");
  hole.setAttribute("stroke", "#4fc3f7");
  hole.setAttribute("stroke-width", "1.5");
  gearGroup.appendChild(hole);

  // 键槽
  const keyW = 8, keyH = 12;
  const keyPath = document.createElementNS(SVG_NS, "path");
  keyPath.setAttribute("d", `M ${CX - keyW/2} ${CY - HOLE_RADIUS} L ${CX - keyW/2} ${CY - HOLE_RADIUS - keyH} L ${CX + keyW/2} ${CY - HOLE_RADIUS - keyH} L ${CX + keyW/2} ${CY - HOLE_RADIUS} Z`);
  keyPath.setAttribute("fill", "#0a0e17");
  keyPath.setAttribute("stroke", "#4fc3f7");
  keyPath.setAttribute("stroke-width", "0.8");
  gearGroup.appendChild(keyPath);

  svg.appendChild(gearGroup);

  // 齿数标注
  const label = document.createElementNS(SVG_NS, "text");
  label.setAttribute("x", CX);
  label.setAttribute("y", CY + 5);
  label.setAttribute("text-anchor", "middle");
  label.setAttribute("dominant-baseline", "middle");
  label.setAttribute("fill", "#4fc3f7");
  label.setAttribute("font-size", "14");
  label.setAttribute("font-family", "monospace");
  label.setAttribute("opacity", "0.6");
  label.textContent = "54T";
  svg.appendChild(label);
}

// ── 动画 ──
function animate() {
  if (rotating) {
    rotationAngle += speed * 0.3;
    if (rotationAngle >= 360) rotationAngle -= 360;
    renderGear();
  }
  animId = requestAnimationFrame(animate);
}

function toggleRotation() {
  rotating = !rotating;
}

function toggleFill() {
  showFill = !showFill;
  renderGear();
}

function changeSpeed(delta) {
  speed = Math.max(0.5, Math.min(5, speed + delta));
}

// ── 启动 ──
renderGear();
animate();
</script>
</body>
</html>
```

## 说明

这是一个 **54齿摆线齿轮** 的交互式 SVG 可视化，包含以下特性：

### 齿形原理
| 部分 | 曲线类型 | 说明 |
|------|---------|------|
| **齿顶 (Addendum)** | 外摆线 (Epicycloid) | 滚动圆在节圆**外侧**滚动生成 |
| **齿根 (Dedendum)** | 内摆线 (Hypocycloid) | 滚动圆在节圆**内侧**滚动生成 |

### 交互功能
- **⏯ 旋转/暂停** — 控制齿轮动画
- **◐ 填充切换** — 切换实体/线框显示
- **+/−** — 调节旋转速度

### 结构细节
- 54 个齿均匀分布（每齿 6.67°）
- 6 根轮辐 + 轮毂 + 中心孔 + 键槽
- 紫色虚线标注节圆位置

将代码保存为 `.html` 文件用浏览器打开即可查看动画效果。