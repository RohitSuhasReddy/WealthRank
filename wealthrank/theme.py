"""WealthRank visual system — Space Black / Mellow White / Burnt Orange."""
import html

import streamlit as st


def inject_css() -> None:
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,400;0,600;1,400;1,500&display=swap');
:root{
  --space:#000000; --mellow:#FEFFFA; --burnt:#D23A00;
  --line:rgba(254,255,250,.13); --muted:rgba(254,255,250,.56);
  --panel:#12100f; --surface:#1b1512;
}
html{scroll-behavior:smooth}
body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{
 background:var(--space)!important;color:var(--mellow)!important;
 font-family:'DM Sans',sans-serif!important;
}
[data-testid="stHeader"]{background:rgba(0,0,0,0)!important}
[data-testid="stMain"]{background:
 radial-gradient(ellipse 65% 25% at 93% 3%,rgba(210,58,0,.14),transparent),
 radial-gradient(ellipse 42% 35% at 0% 48%,rgba(210,58,0,.045),transparent),
 var(--space);}
.block-container{max-width:1360px!important;padding-top:1.25rem!important;padding-left:2.8rem!important;padding-right:2.8rem!important;padding-bottom:7rem!important}
h1,h2,h3,h4,h5,p,li,label,span{font-family:'DM Sans',sans-serif}
h1,h2,h3{letter-spacing:-.045em}
[data-testid="stSidebar"]{background:#0f0d0c!important}
hr{border-color:var(--line)!important}
a{color:var(--mellow)}
::selection{background:var(--burnt);color:var(--mellow)}
[data-testid="stToolbar"],#MainMenu,footer{visibility:hidden}
/* Brand navigation */
.wr-nav{position:relative;z-index:5;display:flex;align-items:center;justify-content:space-between;gap:18px;
  border-bottom:1px solid var(--line);padding:15px 2px 21px}
.wr-logo{font-weight:800;font-size:22px;letter-spacing:-1px;color:var(--mellow);display:flex;align-items:center;gap:10px}
.wr-mark{width:27px;height:27px;background:var(--burnt);display:inline-block;border-radius:6px 2px 8px 2px;
 box-shadow:0 0 28px rgba(210,58,0,.45);transform:rotate(-8deg);position:relative}
.wr-mark:after{content:'';position:absolute;inset:8px 4px 5px 10px;background:var(--space);border-radius:2px;transform:rotate(12deg)}
.wr-links{display:flex;gap:29px;align-items:center}
.wr-links a{font-size:12px;font-weight:600;text-decoration:none;letter-spacing:.04em;opacity:.66;transition:opacity .25s,color .25s}
.wr-links a:hover{opacity:1;color:#EF7041}
.wr-tag{border:1px solid var(--line);border-radius:50px;padding:10px 16px;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
.wr-dot{display:inline-block;width:7px;height:7px;background:var(--burnt);border-radius:50%;margin-right:9px;box-shadow:0 0 12px var(--burnt);animation:pulse 2.5s infinite}
/* Editorial hero */
.wr-hero{min-height:590px;display:grid;grid-template-columns:1.12fr .88fr;position:relative;align-items:center;
 overflow:hidden;border-bottom:1px solid var(--line)}
.wr-hero:before{content:'';position:absolute;pointer-events:none;inset:0;background:
 linear-gradient(90deg,rgba(0,0,0,.9) 0%,rgba(0,0,0,.3) 66%,transparent 100%);z-index:1}
.wr-hero-content{position:relative;z-index:3;max-width:740px;padding:50px 0 65px}
.wr-overline{display:flex;align-items:center;gap:11px;color:var(--mellow);font-size:10px;letter-spacing:.25em;font-weight:700;text-transform:uppercase;margin-bottom:35px}
.wr-overline:before{content:'';width:28px;height:1px;background:var(--burnt)}
.wr-hero-title{font-size:clamp(55px,6.8vw,105px);line-height:.98;font-weight:500;letter-spacing:-.075em;margin:0!important;color:var(--mellow)}
.wr-hero-title .accent{color:var(--burnt)}
.wr-hero-title em{font-family:'Playfair Display',Georgia,serif;font-size:.91em;letter-spacing:-.07em;font-weight:400;color:var(--mellow)}
.wr-hero-description{max-width:460px;color:rgba(254,255,250,.64);font-size:15px;line-height:1.85;margin:31px 0 0}
.wr-hero-bottom{display:flex;align-items:center;gap:25px;margin-top:35px}
.wr-hero-cta{display:inline-flex;align-items:center;gap:19px;background:var(--burnt);color:var(--mellow)!important;
 text-decoration:none!important;border-radius:80px;padding:17px 22px;font-size:12px;font-weight:700;
 position:relative;isolation:isolate;overflow:hidden;transition:transform .35s cubic-bezier(.2,1.4,.5,1),box-shadow .35s}
.wr-hero-cta:before{content:'';position:absolute;inset:-120%;border-radius:45%;z-index:-1;
 background:radial-gradient(circle at 60% 40%,rgba(255,175,120,.6),transparent 38%);
 animation:liquid 6s linear infinite}
.wr-hero-cta:hover{transform:translateY(-4px) scale(1.025);box-shadow:0 12px 50px rgba(210,58,0,.34)}
.wr-arrow{display:grid;place-items:center;border-radius:50%;background:var(--mellow);color:var(--space);width:29px;height:29px;font-size:18px}
.wr-hero-note{font-size:11px;color:var(--muted);letter-spacing:.06em}
.wr-orb-wrap{position:absolute;right:-5%;top:1%;bottom:0;width:61%;z-index:0;display:grid;place-items:center;opacity:1}
.wr-orb{height:min(44vw,550px);width:min(44vw,550px);border-radius:50%;position:relative;
 background:radial-gradient(circle at 34% 25%,#FFAE54 0%,#E85B13 13%,#8C2005 37%,#260A05 62%,#060302 73%);
 box-shadow:inset -50px -55px 100px rgba(0,0,0,.9),0 0 120px rgba(210,58,0,.16);
 animation:orbBreath 8s ease-in-out infinite}
.wr-orb:before{content:'';position:absolute;inset:18% -17%;border:13px solid #FF6A14;border-radius:50%;
 transform:rotate(-29deg);box-shadow:0 0 17px #FF5108,0 0 80px rgba(210,58,0,.7),inset 0 0 25px #EF4A09;
 filter:drop-shadow(0 0 8px #FF7A2C);animation:ringTilt 10s ease-in-out infinite}
.wr-orb:after{content:'';position:absolute;inset:-15%;background:
 repeating-linear-gradient(90deg,transparent 0,transparent 57px,rgba(254,255,250,.07) 58px,transparent 59px);
 opacity:.38;pointer-events:none;mask-image:linear-gradient(90deg,transparent,black)}
.wr-orb-grid{position:absolute;inset:0;background:radial-gradient(circle at 72% 50%,rgba(210,58,0,.4),transparent 48%);filter:blur(80px)}
.wr-floating{position:absolute;z-index:2;border:1px solid rgba(254,255,250,.18);background:rgba(16,10,9,.68);backdrop-filter:blur(12px);
 border-radius:12px;padding:13px 16px;color:var(--mellow);font-size:11px;letter-spacing:.11em;box-shadow:0 20px 45px rgba(0,0,0,.45)}
.wr-floating.top{right:10%;top:16%}.wr-floating.bottom{right:4%;bottom:15%}
.wr-floating strong{display:block;color:#EF754B;font-size:19px;letter-spacing:-.02em;margin-top:4px}
.wr-strip{display:flex;gap:28px;justify-content:space-between;padding:27px 0 36px;border-bottom:1px solid var(--line)}
.wr-strip-item{display:flex;align-items:center;gap:13px;font-size:11px;letter-spacing:.085em;text-transform:uppercase;font-weight:600;color:var(--muted)}
.wr-strip-index{color:var(--burnt);font-weight:800}
.wr-section-head{display:flex;justify-content:space-between;align-items:end;gap:35px;margin:85px 0 28px}
.wr-section-label{color:#EB6941;letter-spacing:.21em;font-size:10px;font-weight:800;margin:0 0 16px}
.wr-section-title{font-size:clamp(38px,4.2vw,63px);font-weight:500;line-height:1.03;letter-spacing:-.065em;margin:0!important;color:var(--mellow)}
.wr-section-title em{font-family:'Playfair Display',Georgia,serif;font-weight:400;color:var(--burnt)}
.wr-section-description{font-size:13px;color:var(--muted);max-width:340px;line-height:1.75}
.wr-caption{font-size:12px;color:var(--muted);line-height:1.7;margin:4px 0 14px}
.wr-miniheading{font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin:12px 0 18px}
.wr-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0 27px}
.wr-metric{border:1px solid var(--line);background:linear-gradient(135deg,#18120E,#090808);border-radius:15px;padding:21px 23px;min-height:134px;position:relative;overflow:hidden;transition:border-color .28s,transform .3s}
.wr-metric:hover{transform:translateY(-5px);border-color:rgba(210,58,0,.65)}
.wr-metric:after{content:'';position:absolute;width:120px;height:120px;border-radius:50%;right:-70px;top:-74px;background:rgba(210,58,0,.10);filter:blur(13px)}
.wr-metric-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.16em;margin-bottom:18px}
.wr-metric-value{font-size:clamp(25px,2.8vw,38px);letter-spacing:-.06em;font-weight:600;line-height:1.1}
.wr-metric-foot{font-size:10px;color:#B7A9A3;margin-top:13px}
.wr-accent{color:#ED7044}
.wr-panel-head{font-size:13px;font-weight:700;letter-spacing:-.01em;margin:7px 0 12px}
.wr-note{padding:17px 21px;border-left:2px solid var(--burnt);background:rgba(210,58,0,.09);font-size:12px;line-height:1.6;color:var(--muted);margin:13px 0 22px}
.wr-rec{border:1px solid var(--line);border-radius:16px;background:linear-gradient(112deg,#17100D,#050505);
 padding:22px 25px;margin:9px 0;transition:transform .3s,border-color .3s}
.wr-rec:hover{transform:translateX(6px);border-color:rgba(210,58,0,.65)}
.wr-rec-top{display:flex;justify-content:space-between;gap:15px;align-items:center}
.wr-rec-name{font-size:19px;font-weight:600;letter-spacing:-.04em}
.wr-rec-score{font-size:20px;color:#ED7044;font-weight:800}
.wr-rec-meta{margin-top:11px;font-size:11px;color:var(--muted);line-height:1.7}
.wr-rec-explain{margin-top:11px;font-size:12px;color:var(--mellow)}
.wr-footer{border-top:1px solid var(--line);padding:35px 0;margin-top:100px;display:flex;justify-content:space-between;gap:20px;font-size:11px;color:var(--muted)}
.wr-fade{animation:fadeUp 1s both}.wr-fade.d2{animation-delay:.18s}.wr-fade.d3{animation-delay:.34s}.wr-fade.d4{animation-delay:.5s}
@keyframes fadeUp{from{opacity:0;transform:translateY(25px);filter:blur(7px)}to{opacity:1;transform:translateY(0);filter:blur(0)}}
@keyframes pulse{50%{opacity:.4;box-shadow:0 0 3px var(--burnt)}}
@keyframes liquid{to{transform:rotate(360deg)}}
@keyframes orbBreath{50%{transform:scale(1.045);filter:saturate(1.25)}}
@keyframes ringTilt{50%{transform:rotate(-24deg) skewY(5deg)}}
@keyframes viewReveal{from{opacity:.2;transform:translateY(25px)}to{opacity:1;transform:translateY(0)}}
@supports (animation-timeline:view()){
 .wr-section-head,.wr-metrics,.wr-rec{animation:viewReveal linear both;animation-timeline:view();animation-range:entry 0% cover 22%}
}
/* Streamlit controls */
[data-testid="stVerticalBlockBorderWrapper"]>div{border-color:var(--line)!important;background:linear-gradient(135deg,#100D0B,#070606)!important;border-radius:16px!important}
[data-testid="stWidgetLabel"] p{font-size:12px!important;color:rgba(254,255,250,.75)!important}
div.stButton>button,div.stDownloadButton>button,button[kind="primary"]{
 border-radius:100px!important;min-height:47px!important;padding:11px 23px!important;
 font-weight:700!important;letter-spacing:.015em!important;transition:transform .28s,box-shadow .28s,border-color .28s,background .28s!important;
}
div.stButton>button:hover,div.stDownloadButton>button:hover{transform:translateY(-3px);box-shadow:0 7px 29px rgba(210,58,0,.25)!important}
button[kind="primary"]{background:radial-gradient(ellipse at 15% 100%,#E8743A 0%,#D23A00 55%,#B52C00 100%)!important;color:var(--mellow)!important;border-color:#F26F3A!important;
 background-size:180% 200%!important;animation:liquidShift 6s ease-in-out infinite}
button[kind="primary"]:hover{background-position:100% 100%!important;box-shadow:0 12px 42px rgba(210,58,0,.39)!important}
@keyframes liquidShift{0%,100%{background-position:0% 0%}50%{background-position:100% 100%}}
button[kind="secondary"]{border:1px solid rgba(254,255,250,.24)!important;background:#1b1411!important;color:var(--mellow)!important}
input,textarea,[data-baseweb="select"]>div,[data-baseweb="input"]>div{background:#181310!important;color:var(--mellow)!important;border-color:rgba(254,255,250,.17)!important;border-radius:9px!important}
[data-testid="stFileUploader"]{border-radius:13px}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border-radius:12px;overflow:hidden}
[data-testid="stMetricValue"]{letter-spacing:-.05em}
[data-testid="stTabs"] button{font-weight:700}
[data-testid="stAlert"]{background:#1b110e!important;border-radius:12px!important}
[data-testid="stExpander"]{border-color:var(--line)!important}
[data-testid="stSlider"] [role="slider"]{background:var(--burnt)!important}
[data-testid="stPlotlyChart"]{background:transparent!important}
@media(max-width:950px){
 .block-container{padding-left:1.2rem!important;padding-right:1.2rem!important}
 .wr-links{display:none}
 .wr-hero{min-height:620px;grid-template-columns:1fr}
 .wr-hero-content{padding-top:55px;align-self:start}
 .wr-hero-title{font-size:clamp(51px,9vw,87px)}
 .wr-orb-wrap{width:74%;right:-22%;top:33%;opacity:.63}
 .wr-orb{width:58vw;height:58vw}
 .wr-metrics{grid-template-columns:repeat(2,1fr)}
 .wr-section-head{margin-top:70px}
}
@media(max-width:600px){
 .wr-nav{padding:14px 0}.wr-logo{font-size:19px}.wr-tag{font-size:9px;padding:9px 11px}
 .wr-hero{min-height:600px}.wr-hero-content{padding-top:65px}
 .wr-hero-title{font-size:clamp(52px,12vw,70px)}
 .wr-hero-description{font-size:13px;max-width:340px}
 .wr-orb-wrap{top:43%;right:-25%;width:90%;opacity:.36}
 .wr-orb{width:88vw;height:88vw}.wr-floating{display:none}
 .wr-strip{flex-wrap:wrap;gap:17px}.wr-strip-item{font-size:9px}
 .wr-section-head{display:block;margin:65px 0 22px}.wr-section-description{margin-top:15px}
 .wr-metrics{gap:8px}.wr-metric{padding:16px;min-height:116px}.wr-metric-value{font-size:26px}
 .wr-footer{display:block;line-height:2}
}
@media(prefers-reduced-motion:reduce){
 *,*:before,*:after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important;scroll-behavior:auto!important}
}
</style>""", unsafe_allow_html=True)


def hero() -> None:
    st.markdown("""
<div class="wr-nav">
  <div class="wr-logo"><span class="wr-mark"></span> WealthRank<span style="color:#D23A00">.</span></div>
  <div class="wr-links">
    <a href="#portfolio">Portfolio</a><a href="#analytics">Analytics</a>
    <a href="#discover">Discover</a><a href="#fire">FIRE</a><a href="#lab">Model Lab</a>
  </div>
  <div class="wr-tag"><span class="wr-dot"></span> Finance intelligence</div>
</div>
<section class="wr-hero">
  <div class="wr-orb-grid"></div>
  <div class="wr-orb-wrap"><div class="wr-orb"></div></div>
  <div class="wr-floating top">DATA-DRIVEN INSIGHT<strong>01 / 05</strong></div>
  <div class="wr-floating bottom">YOUR WEALTH / REIMAGINED<strong>∞ POTENTIAL</strong></div>
  <div class="wr-hero-content">
    <div class="wr-overline wr-fade">WEALTHRANK — INTELLIGENCE FOR PEOPLE</div>
    <h1 class="wr-hero-title wr-fade d2">Technology<br>Crafted for <span class="accent">All</span><br>Not <em>Machines.</em></h1>
    <p class="wr-hero-description wr-fade d3">Understand what you own. Discover what complements it.
    See how your wealth could grow — with transparent data, intentional design, and no paid API keys.</p>
    <div class="wr-hero-bottom wr-fade d4">
      <a class="wr-hero-cta" href="#portfolio">Explore your wealth <span class="wr-arrow">↗</span></a>
      <span class="wr-hero-note">INVESTING, MADE HUMAN</span>
    </div>
  </div>
</section>
<div class="wr-strip">
  <div class="wr-strip-item"><span class="wr-strip-index">01</span> REAL MARKET DATA</div>
  <div class="wr-strip-item"><span class="wr-strip-index">02</span> EXPLAINABLE RANKING</div>
  <div class="wr-strip-item"><span class="wr-strip-index">03</span> RISK-AWARE GUARDRAILS</div>
  <div class="wr-strip-item"><span class="wr-strip-index">04</span> INFLATION-AWARE FIRE</div>
</div>
""", unsafe_allow_html=True)


def section(anchor: str, number: str, label: str, title: str, description: str) -> None:
    st.markdown(
        f'<div id="{html.escape(anchor)}" class="wr-section-head">'
        f'<div><div class="wr-section-label">{html.escape(number)} / {html.escape(label)}</div>'
        f'<h2 class="wr-section-title">{title}</h2></div>'
        f'<div class="wr-section-description">{html.escape(description)}</div></div>',
        unsafe_allow_html=True,
    )


def metrics(items: list[tuple[str, str, str]]) -> None:
    tiles = []
    for label, value, foot in items:
        tiles.append(
            '<div class="wr-metric">'
            f'<div class="wr-metric-label">{html.escape(label)}</div>'
            f'<div class="wr-metric-value">{html.escape(value)}</div>'
            f'<div class="wr-metric-foot">{html.escape(foot)}</div>'
            '</div>'
        )
    st.markdown('<div class="wr-metrics">' + ''.join(tiles) + '</div>',
                unsafe_allow_html=True)


def note(content: str) -> None:
    st.markdown(f'<div class="wr-note">{html.escape(content)}</div>', unsafe_allow_html=True)


def recommendation_card(item: dict, rank: int) -> None:
    st.markdown(
        '<div class="wr-rec">'
        '<div class="wr-rec-top">'
        f'<div><div class="wr-section-label">MATCH {rank:02d} · {html.escape(item["asset_class"])}</div>'
        f'<div class="wr-rec-name">{html.escape(item["name"])}</div></div>'
        f'<div class="wr-rec-score">{item["score"]:.0f}<span style="font-size:11px;color:#AFA29A"> / 100</span></div></div>'
        f'<div class="wr-rec-explain">{html.escape(item["explanation"])}</div>'
        f'<div class="wr-rec-meta">{html.escape(item["sector"])} · Ann. volatility {item["volatility"]:.1%}'
        f' · {html.escape(item["liquidity_note"])} · {html.escape(item["as_of"])}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def footer() -> None:
    st.markdown(
        '<div class="wr-footer"><span>WEALTHRANK © 2026 · BUILT FOR CLARITY, NOT HYPE.</span>'
        '<span>Free public market data · Educational analytics · Not financial advice</span></div>',
        unsafe_allow_html=True,
    )
