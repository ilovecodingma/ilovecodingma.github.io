/* 공용 유틸: 토스트, 시드 난수, 캔버스 줄바꿈, 공유 버튼. 모든 처리는 브라우저 안에서만 이뤄지며 서버 전송 없음. */
(function () {
  var F = window.FUN = {};
  F.$ = function (s, r) { return (r || document).querySelector(s); };
  F.toast = function (m) {
    var t = F.$('#toast');
    if (!t) { t = document.createElement('div'); t.id = 'toast'; t.className = 'toast'; document.body.appendChild(t); }
    t.textContent = m; t.classList.add('on'); clearTimeout(F._t);
    F._t = setTimeout(function () { t.classList.remove('on'); }, 2200);
  };
  F.seed = function (str) {
    var h = 1779033703 ^ str.length;
    for (var i = 0; i < str.length; i++) { h = Math.imul(h ^ str.charCodeAt(i), 3432918353); h = h << 13 | h >>> 19; }
    h = Math.imul(h ^ h >>> 16, 2246822507); h = Math.imul(h ^ h >>> 13, 3266489909); h ^= h >>> 16;
    var a = h >>> 0;
    return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  };
  F.kstDate = function () {
    return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
  };
  F.wrap = function (ctx, text, x, y, maxW, lh, maxLines) {
    var ch = String(text).split(''), line = '', lines = [];
    for (var i = 0; i < ch.length; i++) {
      var t = line + ch[i];
      if (ctx.measureText(t).width > maxW && line) { lines.push(line); line = ch[i]; } else line = t;
    }
    if (line) lines.push(line);
    if (maxLines && lines.length > maxLines) { lines = lines.slice(0, maxLines); lines[maxLines - 1] = lines[maxLines - 1].replace(/.$/, '…'); }
    lines.forEach(function (l, i) { ctx.fillText(l, x, y + i * lh); });
    return y + lines.length * lh;
  };
  F.rr = function (ctx, x, y, w, h, r) {
    ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  };
  F.FONT = '"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif';
  F.prompt = function (t) { window.prompt('아래 내용을 복사하세요', t); };
  F.copy = function (t) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(t).then(function () { F.toast('복사했어요'); }, function () { F.prompt(t); });
    }
    F.prompt(t); return Promise.resolve();
  };
  /* 공유 바: o={title,text,url,canvas:function(){return canvas},file:'name.png'} */
  F.shareBar = function (el, o) {
    el.innerHTML = '<div class="share"><button class="btn sv" data-a="save">결과 이미지 저장</button>' +
      '<button class="btn kk" data-a="kakao">카카오톡 공유</button><button class="btn xx" data-a="x">X(트위터) 공유</button>' +
      '<button class="btn ghost" data-a="copy" style="grid-column:1/-1">링크 복사</button></div>';
    function blob() { var c = o.canvas(); return new Promise(function (r) { c.toBlob(r, 'image/png'); }); }
    el.onclick = function (e) {
      var a = e.target.getAttribute && e.target.getAttribute('data-a'); if (!a) return;
      if (a === 'save') {
        blob().then(function (b) {
          var u = URL.createObjectURL(b), l = document.createElement('a');
          l.href = u; l.download = o.file || 'result.png'; document.body.appendChild(l); l.click(); l.remove();
          setTimeout(function () { URL.revokeObjectURL(u); }, 3000); F.toast('이미지를 저장했어요');
        });
      } else if (a === 'copy') { F.copy(o.url); }
      else if (a === 'x') { window.open('https://twitter.com/intent/tweet?text=' + encodeURIComponent(o.text) + '&url=' + encodeURIComponent(o.url), '_blank', 'noopener'); }
      else if (a === 'kakao') {
        if (navigator.share) {
          blob().then(function (b) {
            var f = new File([b], o.file || 'result.png', { type: 'image/png' });
            var d = { title: o.title, text: o.text, url: o.url };
            if (navigator.canShare && navigator.canShare({ files: [f] })) d.files = [f];
            return navigator.share(d);
          }).catch(function () {});
        } else {
          F.copy(o.text + ' ' + o.url).then(function () { F.toast('복사했어요. 카카오톡 대화창에 붙여넣기 하세요'); });
        }
      }
    };
  };
})();
