/* 홈 배경: WebGL 점 지구본 + 한반도 헬게이트. 라이브러리 없음. 육지 마스크: Natural Earth(퍼블릭 도메인) → land.png.
   모션 줄이기·WebGL 불가·마스크 로드 실패 시 자동으로 꺼짐. */
(function () {
  var c = document.getElementById('ct-bg'); if (!c) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) { c.style.display = 'none'; return; }
  var gl = c.getContext('webgl', { antialias: true, alpha: true, premultipliedAlpha: false });
  if (!gl) { c.style.display = 'none'; return; }
  var small = innerWidth < 700, D2R = Math.PI / 180;
  var KLON = 127.8 * D2R, KLAT = 36.0 * D2R;
  var K = [Math.cos(KLAT) * Math.sin(KLON), Math.sin(KLAT), Math.cos(KLAT) * Math.cos(KLON)];

  /* ── 행렬 ── */
  function mul(a, b) { var o = new Float32Array(16); for (var i = 0; i < 4; i++) for (var j = 0; j < 4; j++) { var s = 0; for (var k = 0; k < 4; k++) s += a[k * 4 + j] * b[i * 4 + k]; o[i * 4 + j] = s; } return o; }
  function rotX(t) { var c_ = Math.cos(t), s = Math.sin(t); return new Float32Array([1, 0, 0, 0, 0, c_, s, 0, 0, -s, c_, 0, 0, 0, 0, 1]); }
  function rotY(t) { var c_ = Math.cos(t), s = Math.sin(t); return new Float32Array([c_, 0, -s, 0, 0, 1, 0, 0, s, 0, c_, 0, 0, 0, 0, 1]); }
  function persp(fy, a, n, f) { var t = 1 / Math.tan(fy / 2); return new Float32Array([t / a, 0, 0, 0, 0, t, 0, 0, 0, 0, (f + n) / (n - f), -1, 0, 0, 2 * f * n / (n - f), 0]); }
  function norm(v) { var l = Math.hypot(v[0], v[1], v[2]); return [v[0] / l, v[1] / l, v[2] / l]; }
  function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }

  /* ── 셰이더 ── */
  function sh(t, s) { var o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) { console.warn(gl.getShaderInfoLog(o)); } return o; }
  function prog(vs, fs) { var p = gl.createProgram(); gl.attachShader(p, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(p); if (!gl.getProgramParameter(p, gl.LINK_STATUS)) { console.warn('link: ' + gl.getProgramInfoLog(p)); return null; } return p; }
  var COMMON = 'uniform mat4 uM,uP;uniform float uShift,uDist,uT,uPx,uOpen;';
  var PROJ = 'vec4 proj(vec3 w){vec4 v=vec4(w,1.0);v.z-=uDist;vec4 cp=uP*v;cp.x+=uShift*cp.w;return cp;}';

  // 1) 점(육지·바다)
  var pDots = prog(
    'attribute vec3 p;attribute vec3 a;' + COMMON + PROJ + 'varying vec4 vc;' +
    'void main(){vec4 w=uM*vec4(p,1.0);vec3 n=(uM*vec4(p,0.0)).xyz;float front=smoothstep(-0.12,0.22,n.z);' +
    'gl_Position=proj(w.xyz);float rim=pow(1.0-max(n.z,0.0),2.0);' +
    'vec3 base=mix(vec3(.68,.78,1.0),vec3(.95,.97,1.0),rim);float pulse=.5+.5*sin(uT*3.0+a.z*6.2832);' +
    'vec3 hot=mix(vec3(1.0,.16,.08),vec3(1.0,.72,.2),pulse*.55);float hk=a.x*smoothstep(0.0,1.5,uOpen+.4);vec3 col=mix(base,hot,hk);' +
    'float land=1.0-a.y;float al=(land*1.0+a.y*.06)*mix(.05,1.0,front);al*=1.0+a.x*.35;vc=vec4(col,al);' +
    'gl_PointSize=(land*(1.2+front*1.7+a.x*4.2)+a.y*1.2)*uPx;}',
    'precision mediump float;varying vec4 vc;void main(){vec2 q=gl_PointCoord-.5;float r=length(q);if(r>.5)discard;gl_FragColor=vec4(vc.rgb,vc.a*(1.0-r*1.7));}'
  );
  // 2) 대기(후광)
  var pAtm = prog(
    'attribute vec2 q;' + COMMON + PROJ + 'varying vec2 uv;void main(){uv=q;gl_Position=proj(vec3(q*1.9,0.0));}',
    'precision highp float;varying vec2 uv;uniform float uDist,uOpen,uT;void main(){float r=length(uv)*1.9;float rs=uDist/sqrt(uDist*uDist-1.0);' +
    'float outside=exp(-max(r-rs,0.0)*7.0)*step(rs,r);float inside=smoothstep(rs,rs*.55,r);' +
    'vec3 glow=mix(vec3(.28,.34,.95),vec3(.95,.2,.45),smoothstep(-.6,.9,uv.x-uv.y*.3));' +
    'float a=outside*.55+inside*.10;a+=outside*uOpen*.18;gl_FragColor=vec4(glow,a);}'
  );
  // 3) 헬게이트
  var pGate = prog(
    'attribute vec3 p;attribute vec2 q;' + COMMON + PROJ + 'varying vec2 uv;void main(){uv=q;gl_Position=proj((uM*vec4(p,1.0)).xyz);}',
    'precision highp float;varying vec2 uv;uniform float uT,uOpen;' +
    'float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}' +
    'float vn(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}' +
    'float fbm(vec2 p){float s=0.,a=.5;for(int i=0;i<4;i++){s+=a*vn(p);p*=2.03;a*=.5;}return s;}' +
    'void main(){float r=length(uv)*1.5;if(length(uv)>1.0)discard;float th=atan(uv.y,uv.x);float o=uOpen;float R=o*(.86+.07*vn(vec2(th*4.0,uT*.4))+.05*vn(vec2(th*13.0,3.0)));' +
    'float sw=th+2.4/(r+.16)-uT*1.15;float bands=.5+.5*sin(sw*4.0);float n=fbm(vec2(sw*1.2,r*5.0-uT*.7));' +
    'float inD=smoothstep(R,R-.1,r);float core=smoothstep(.44*o,.30*o,r);' +
    'vec3 lava=mix(vec3(.28,.0,.02),vec3(1.0,.26,.04),clamp(bands*n*1.7,0.,1.));lava=mix(lava,vec3(1.0,.82,.32),pow(clamp(bands*n,0.,1.),3.0)*.9);' +
    'vec3 col=lava*inD;col=mix(col,vec3(0.0),core);' +
    'float rim=smoothstep(.07,.0,abs(r-R))*o;col+=vec3(1.0,.22,.08)*rim*1.5;' +
    'float halo=exp(-max(r-R,0.0)*6.0)*o*(1.0-inD);col+=vec3(1.0,.12,.14)*halo*.95;' +
    'float ang=(th+3.14159)/6.28318*22.0;float id=floor(ang);float f=fract(ang);float len=(.45+.55*h(vec2(id,3.0)))*o;' +
    'float ray=smoothstep(.10,.0,abs(f-.5))*smoothstep(R-.04,R+.04,r)*smoothstep(R+len*.9,R+.05,r);' +
    'col+=vec3(1.0,.52,.2)*ray*(.55+.45*sin(uT*6.0+id*2.0))*o;' +
    'float rimIn=smoothstep(.07,.0,abs(r-.40*o))*o;col+=vec3(1.0,.3,.1)*rimIn*1.4;float a=clamp(inD*.97*(1.0-core)+halo+rim+ray+rimIn,0.,1.);a*=smoothstep(0.0,.2,o);gl_FragColor=vec4(col,a);}'
  );
  // 4) 불씨
  var pEmb = prog(
    'attribute vec3 s;' + COMMON + PROJ + 'uniform vec3 uK,uE,uU;uniform float uSize;varying vec4 vc;' +
    'void main(){float age=fract(uT*(.16+s.x*.2)+s.x*7.0);float sp=1.0+age*1.1;' +
    'vec3 pos=uK*(1.003+age*.55)+uE*(s.y-.5)*1.7*uSize*sp+uU*(s.z-.5)*1.7*uSize*sp;' +
    'vec4 w=uM*vec4(pos,1.0);gl_Position=proj(w.xyz);float life=1.0-age;vec3 c=mix(vec3(1.0,.2,.05),vec3(1.0,.8,.3),life*life);' +
    'vc=vec4(c,life*uOpen*.95);gl_PointSize=(1.2+life*3.2)*uPx;}',
    'precision mediump float;varying vec4 vc;void main(){vec2 q=gl_PointCoord-.5;float r=length(q);if(r>.5)discard;gl_FragColor=vec4(vc.rgb,vc.a*(1.0-r*1.9));}'
  );
  if (!pDots || !pAtm || !pGate || !pEmb) { console.warn('globe: shader 실패', !!pDots, !!pAtm, !!pGate, !!pEmb); c.style.display = 'none'; return; }

  /* ── 육지 마스크 불러와 점 만들기 ── */
  var img = new Image();
  img.onerror = function () { console.warn('globe: land.png 로드 실패'); c.style.display = 'none'; };
  img.onload = build;
  img.src = '/assets/home/land.png?v=1';

  function build() {
    var cv = document.createElement('canvas'); cv.width = img.width; cv.height = img.height;
    var cx = cv.getContext('2d'); cx.drawImage(img, 0, 0); var dat = cx.getImageData(0, 0, cv.width, cv.height).data, W = cv.width, H = cv.height;
    function land(lon, lat) { var x = Math.floor((lon + 180) / 360 * W) % W, y = Math.min(H - 1, Math.max(0, Math.floor((90 - lat) / 180 * H))); return dat[(y * W + x) * 4] > 128; }
    var step = small ? 1.15 : 0.8, pts = [], rnd = function () { return Math.random(); };
    function addDot(lon, lat, kind) {
      var la = lat * D2R, lo = lon * D2R, p = [Math.cos(la) * Math.sin(lo), Math.sin(la), Math.cos(la) * Math.cos(lo)];
      var dot = p[0] * K[0] + p[1] * K[1] + p[2] * K[2], ang = Math.acos(Math.min(1, dot)) / D2R;
      var kw = kind === 0 ? Math.max(0, Math.min(1, (7.5 - ang) / 4.5)) : 0;
      pts.push(p[0], p[1], p[2], kw, kind, rnd());
    }
    for (var lat = -78; lat <= 84; lat += step) {
      var ls = step / Math.max(0.12, Math.cos(lat * D2R));
      for (var lon = -180; lon < 180; lon += ls) { if (land(lon, lat)) addDot(lon, lat, 0); }
    }
    // 한반도에서 사방으로 갈라지는 용암 균열(구면 위 랜덤 워크)
    (function () {
      var kn0 = norm(K), e0 = norm(cross([0, 1, 0], kn0)), u0 = cross(kn0, e0), NC = small ? 14 : 22;
      for (var ci = 0; ci < NC; ci++) {
        var ang0 = ci / NC * 6.2832 + rnd() * .25, p = kn0.slice(), tdir = [e0[0] * Math.cos(ang0) + u0[0] * Math.sin(ang0), e0[1] * Math.cos(ang0) + u0[1] * Math.sin(ang0), e0[2] * Math.cos(ang0) + u0[2] * Math.sin(ang0)];
        var len = (12 + rnd() * 26) * D2R, st = .006, steps = Math.floor(len / st), br = rnd() * .5;
        for (var si = 0; si < steps; si++) {
          if (si > 14) pts.push(p[0], p[1], p[2], 1, 0, rnd());
          p = norm([p[0] + tdir[0] * st, p[1] + tdir[1] * st, p[2] + tdir[2] * st]);
          var d = tdir[0] * p[0] + tdir[1] * p[1] + tdir[2] * p[2]; tdir = [tdir[0] - p[0] * d, tdir[1] - p[1] * d, tdir[2] - p[2] * d];
          var jx = (rnd() - .5) * .22, rv = cross(p, tdir); tdir = norm([tdir[0] + rv[0] * jx, tdir[1] + rv[1] * jx, tdir[2] + rv[2] * jx]);
          if (si === Math.floor(steps * (.35 + br * .3)) && rnd() < .8) {   // 갈라지는 가지
            var q = p.slice(), td2 = norm([tdir[0] * .8 + rv[0] * .6, tdir[1] * .8 + rv[1] * .6, tdir[2] * .8 + rv[2] * .6]);
            for (var bi = 0; bi < steps * .45; bi++) { q = norm([q[0] + td2[0] * st, q[1] + td2[1] * st, q[2] + td2[2] * st]); var dd = td2[0] * q[0] + td2[1] * q[1] + td2[2] * q[2]; td2 = norm([td2[0] - q[0] * dd + (rnd() - .5) * .15, td2[1] - q[1] * dd + (rnd() - .5) * .15, td2[2] - q[2] * dd + (rnd() - .5) * .15]); pts.push(q[0], q[1], q[2], 1, 0, rnd()); }
          }
        }
      }
    })();
    var nOcean = small ? 1200 : 2600;
    for (var i = 0; i < nOcean; i++) { var u = rnd() * 2 - 1, th = rnd() * 6.2832, r = Math.sqrt(1 - u * u); var la2 = Math.asin(u) / D2R, lo2 = th / D2R - 180; if (!land(lo2, la2)) addDot(lo2, la2, 1); }
    var dotBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, dotBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(pts), gl.STATIC_DRAW);
    var nDots = pts.length / 6;

    var qBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, qBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);

    // 게이트: 한반도에서 바깥을 보는 정사각형
    var kn = norm(K), e = norm(cross([0, 1, 0], kn)), u2 = cross(kn, e), GS = small ? 0.36 : 0.44, g = [];
    [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(function (q) {
      g.push(kn[0] * 1.004 + (e[0] * q[0] + u2[0] * q[1]) * GS, kn[1] * 1.004 + (e[1] * q[0] + u2[1] * q[1]) * GS, kn[2] * 1.004 + (e[2] * q[0] + u2[2] * q[1]) * GS, q[0], q[1]);
    });
    var gBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, gBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(g), gl.STATIC_DRAW);

    var NE = small ? 160 : 420, em = []; for (var j = 0; j < NE; j++) em.push(rnd(), rnd(), rnd());
    var eBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, eBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(em), gl.STATIC_DRAW);

    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    var mx = 0, my = 0, tx = 0, ty = 0, run = true, dpr = Math.min(window.devicePixelRatio || 1, small ? 1.5 : 2), t0 = performance.now();
    function size() { var w = c.clientWidth, h = c.clientHeight; c.width = Math.max(2, w * dpr); c.height = Math.max(2, h * dpr); gl.viewport(0, 0, c.width, c.height); }
    size(); addEventListener('resize', size);
    addEventListener('pointermove', function (ev) { tx = ev.clientX / innerWidth - .5; ty = ev.clientY / innerHeight - .5; }, { passive: true });
    document.addEventListener('visibilitychange', function () { run = !document.hidden; if (run) requestAnimationFrame(frame); });

    function setU(p, o) { for (var k in o) { var l = gl.getUniformLocation(p, k); if (l === null) continue; var v = o[k]; if (v.length === 16) gl.uniformMatrix4fv(l, false, v); else if (v.length === 3) gl.uniform3fv(l, v); else gl.uniform1f(l, v); } }
    function attr(p, name, n, stride, off) { var l = gl.getAttribLocation(p, name); if (l < 0) return; gl.enableVertexAttribArray(l); gl.vertexAttribPointer(l, n, gl.FLOAT, false, stride * 4, off * 4); }
    function ease(x) { x = Math.max(0, Math.min(1, x)); return 1 - Math.pow(1 - x, 3); }

    function frame(now) {
      if (!run) return;
      var FT = /[?&]gt=([\d.]+)/.exec(location.search); var t = FT ? parseFloat(FT[1]) : (now - t0) / 1000; mx += (tx - mx) * .05; my += (ty - my) * .05;
      var open = t < 1.4 ? 0 : (t < 4.6 ? ease((t - 1.4) / 3.2) * 0.96 : 0.96 + 0.04 * Math.sin(t * 2.1));
      var spin = (1 - ease(t / 3.6)) * 2.6;                       // 처음엔 돌다가 한반도 쪽으로 멈춤
      var yaw = -KLON + spin + mx * .35 + Math.sin(t * .25) * .06, pitch = KLAT + my * .2;
      var M = mul(rotX(pitch), rotY(yaw));
      var aspect = c.width / c.height, P = persp(36 * D2R, aspect, .1, 20);
      var shift = small ? 0.0 : 0.38;
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
      var common = { uM: M, uP: P, uShift: shift, uDist: 3.7, uT: t, uPx: dpr, uOpen: open };

      gl.useProgram(pAtm); setU(pAtm, common); gl.bindBuffer(gl.ARRAY_BUFFER, qBuf); attr(pAtm, 'q', 2, 2, 0); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      gl.useProgram(pDots); setU(pDots, common); gl.bindBuffer(gl.ARRAY_BUFFER, dotBuf); attr(pDots, 'p', 3, 6, 0); attr(pDots, 'a', 3, 6, 3); gl.drawArrays(gl.POINTS, 0, nDots);
      gl.useProgram(pGate); setU(pGate, common); gl.bindBuffer(gl.ARRAY_BUFFER, gBuf); attr(pGate, 'p', 3, 5, 0); attr(pGate, 'q', 2, 5, 3); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      gl.useProgram(pEmb); var ce = common; ce.uK = kn; ce.uE = e; ce.uU = u2; ce.uSize = GS; setU(pEmb, ce); gl.bindBuffer(gl.ARRAY_BUFFER, eBuf); attr(pEmb, 's', 3, 3, 0); gl.drawArrays(gl.POINTS, 0, NE);
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
})();
