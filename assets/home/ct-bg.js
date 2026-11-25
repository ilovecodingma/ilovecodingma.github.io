/* 수험 홈 배경: 가벼운 WebGL 점 파도(3D). 라이브러리 없음. 모션 줄이기·WebGL 불가 시 자동 꺼짐. */
(function(){
  var c=document.getElementById('ct-bg'); if(!c) return;
  if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches){c.style.display='none';return}
  var gl=c.getContext('webgl',{antialias:false,alpha:true,premultipliedAlpha:false}); if(!gl){c.style.display='none';return}
  var small=innerWidth<700, N=small?36:64, pts=[];
  for(var i=0;i<N;i++)for(var j=0;j<N;j++)pts.push((i/(N-1)-.5)*11,(j/(N-1)-.5)*11);
  var vs='attribute vec2 p;uniform float t,asp,px;uniform vec2 m;varying float d;'+
  'void main(){float x=p.x,z=p.y;float y=sin(x*1.1+t*.55)*.42+cos(z*.9+t*.45)*.42+sin((x+z)*.6+t*.3)*.3;'+
  'float a=.25+m.x*.18,cx=cos(a),sx=sin(a);vec3 v=vec3(x*cx-z*sx,y,x*sx+z*cx);'+
  'float b=-.62+m.y*.1,cb=cos(b),sb=sin(b);v=vec3(v.x,v.y*cb-v.z*sb,v.y*sb+v.z*cb);v.z+=6.2;v.y+=.2;'+
  'gl_Position=vec4(v.x*2.6/asp,v.y*2.6,0.,v.z);d=clamp((v.z-3.)/7.,0.,1.);gl_PointSize=(2.4+(1.-d)*4.2)*px;}';
  var fs='precision mediump float;varying float d;void main(){vec2 q=gl_PointCoord-.5;float r=length(q);if(r>.5)discard;'+
  'vec3 c=mix(vec3(.55,.62,1.),vec3(.85,.25,.55),d*.6);gl_FragColor=vec4(c,(.35+(1.-d)*.65)*(1.-r*1.5));}';
  function sh(t,s){var o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);return o}
  var pr=gl.createProgram();gl.attachShader(pr,sh(gl.VERTEX_SHADER,vs));gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(pr);
  if(!gl.getProgramParameter(pr,gl.LINK_STATUS)){c.style.display='none';return}
  gl.useProgram(pr);var buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(pts),gl.STATIC_DRAW);
  var lp=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(lp);gl.vertexAttribPointer(lp,2,gl.FLOAT,false,0,0);
  var U=function(n){return gl.getUniformLocation(pr,n)},ut=U('t'),ua=U('asp'),um=U('m'),up=U('px');
  gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
  var mx=0,my=0,tx=0,ty=0,run=true,dpr=Math.min(devicePixelRatio||1,small?1.5:2);
  function size(){var w=c.clientWidth,h=c.clientHeight;c.width=w*dpr;c.height=h*dpr;gl.viewport(0,0,c.width,c.height)}
  size();addEventListener('resize',size);
  addEventListener('pointermove',function(e){tx=e.clientX/innerWidth-.5;ty=e.clientY/innerHeight-.5},{passive:true});
  document.addEventListener('visibilitychange',function(){run=!document.hidden;if(run)req()});
  var t0=performance.now();
  function frame(now){if(!run)return;mx+=(tx-mx)*.04;my+=(ty-my)*.04;gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);
    gl.uniform1f(ut,(now-t0)/1000);gl.uniform1f(ua,c.width/c.height);gl.uniform2f(um,mx,my);gl.uniform1f(up,dpr);
    gl.drawArrays(gl.POINTS,0,N*N);req()}
  function req(){requestAnimationFrame(frame)}req();
})();
