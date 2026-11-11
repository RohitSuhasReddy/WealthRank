"""Interactive universe navigation: planets are NATIVE Streamlit buttons.

Using Streamlit callbacks instead of raw <a> page reloads preserves the
in-memory portfolio, risk selections and recommendation cache.
"""
from __future__ import annotations

import streamlit as st


PAGES = {
    "home": ("Universe", "✧"),
    "portfolio": ("Portfolio", "◉"),
    "analytics": ("Stock Analytics", "⌁"),
    "discover": ("Discover", "✦"),
    "fire": ("FIRE Planner", "↗"),
    "lab": ("Model Lab", "⬡"),
}


def navigate(page: str) -> None:
    if page not in PAGES:
        page = "home"
    st.session_state["active_page"] = page
    # State remains intact because the callback reruns this Streamlit session.
    st.query_params["view"] = page


def current_page() -> str:
    if "active_page" not in st.session_state:
        deep_link = str(st.query_params.get("view", "home"))
        st.session_state["active_page"] = deep_link if deep_link in PAGES else "home"
    return st.session_state["active_page"]


def inject_navigation_css() -> None:
    st.markdown("""<style>
.wr-homebrand{display:flex;align-items:center;gap:11px;border-bottom:1px solid rgba(254,255,250,.12);padding:8px 2px 15px;color:#FEFFFA;font-size:19px;font-weight:800;letter-spacing:-.06em}.wr-homebrand b{color:#D23A00}.wr-homebrand small{font-size:9px;font-weight:600;letter-spacing:.14em;color:#9C8E85;margin-left:auto}
.wr-sitebar{display:flex;align-items:center;gap:10px;padding:6px 0}
.wr-sitebrand{font-size:24px;font-weight:800;letter-spacing:-.07em;color:#FEFFFA;white-space:nowrap}
.wr-sitebrand b{color:#D23A00}.wr-sitebrand small{font-size:9px;letter-spacing:.16em;color:#8E817C;display:block;font-weight:600}
.st-key-app_nav{padding:10px 0 19px;border-bottom:1px solid #35231e;margin-bottom:12px}
.st-key-app_nav button{min-height:41px!important;font-size:11px!important;font-weight:700!important;padding:6px 8px!important}
.wr-space-head{position:relative;z-index:3;max-width:880px;text-align:center;margin:22px auto 11px}
.wr-space-overline{font-size:10px;letter-spacing:.23em;font-weight:800;color:#EF794D;text-transform:uppercase;animation:wr-arrive .8s ease both}
.wr-space-title{font-size:clamp(50px,6vw,81px)!important;line-height:1.05!important;font-weight:500;letter-spacing:-.07em;margin:12px auto 18px!important;color:#FEFFFA;animation:wr-arrive 1s ease both}
.wr-space-title em{font-family:'Playfair Display',Georgia,serif;font-weight:400;color:#E96834}
.wr-space-sub{color:#BBAEA8;font-size:14px;line-height:1.7;max-width:600px;margin:0 auto;animation:wr-arrive 1.2s ease both}
/* The previous absolute-positioned Streamlit widgets caused the screenshot's broken layout.
   Three real rows and columns now determine every planet position. */
.st-key-universe{position:relative!important;isolation:isolate;max-width:1050px;margin:7px auto 0!important;padding:7px 28px 10px!important;overflow:visible!important;background:radial-gradient(ellipse at 50% 50%,rgba(210,58,0,.16),transparent 66%)}
.st-key-universe::before,.st-key-universe::after{content:"";position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-19deg);border:1px solid rgba(254,255,250,.18);border-radius:50%;pointer-events:none;z-index:0}
.st-key-universe::before{width:92%;height:300px}
.st-key-universe::after{width:71%;height:235px;border-color:rgba(210,58,0,.36);transform:translate(-50%,-50%) rotate(22deg)}
.wr-starfield{position:absolute;inset:0;pointer-events:none;z-index:0;opacity:.56;background-image:radial-gradient(circle at 9% 19%,#FEFFFA 1px,transparent 2px),radial-gradient(circle at 88% 14%,#FEFFFA 1px,transparent 2px),radial-gradient(circle at 22% 76%,#D23A00 1px,transparent 2px),radial-gradient(circle at 80% 87%,#FEFFFA 1px,transparent 2px)}
.st-key-solar_row_top,.st-key-solar_row_middle,.st-key-solar_row_bottom{position:relative!important;z-index:2}
.st-key-solar_row_top{min-height:106px}.st-key-solar_row_middle{min-height:185px}.st-key-solar_row_bottom{min-height:108px}
.st-key-universe [data-testid="stHorizontalBlock"]{align-items:center!important}
.wr-sun-shell{height:182px;display:flex;align-items:center;justify-content:center;pointer-events:none;position:relative}
.wr-sun{width:160px;height:160px;position:relative;flex:none;border-radius:50%;background:radial-gradient(circle at 27% 22%,#FFD3A7,#F56C20 16%,#B7350D 42%,#2E1007 78%,#070303);box-shadow:0 0 28px rgba(255,91,23,.64),0 0 100px rgba(210,58,0,.23),inset -22px -32px 50px #170703;animation:wr-breathe 8s ease-in-out infinite}
.wr-sun::before{content:"";position:absolute;inset:24% -22%;transform:rotate(-27deg);border-radius:50%;border:7px solid #FF7526;box-shadow:0 0 20px #F96516,0 0 52px #9F2708;animation:wr-ring 12s ease-in-out infinite}
.wr-sun-inner{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;text-align:center;font-size:13px;letter-spacing:.13em;font-weight:800;color:#FEFFFA;text-shadow:0 2px 9px #190704}
.wr-sun-inner span{font-size:8px;letter-spacing:.1em;color:#F4CBAC;margin-top:9px}
.st-key-universe [class*="st-key-planet_"]{width:100%!important;display:flex!important;align-items:center!important;justify-content:center!important;z-index:5;position:relative!important;overflow:visible!important}
.st-key-universe [class*="st-key-planet_"] button{height:114px!important;width:114px!important;min-height:114px!important;min-width:114px!important;padding:12px!important;margin:auto!important;border-radius:50%!important;display:flex!important;align-items:center!important;justify-content:center!important;text-align:center!important;white-space:normal!important;line-height:1.4!important;font-size:12px!important;font-weight:800!important;color:#FEFFFA!important;border:1px solid rgba(254,255,250,.42)!important;background:radial-gradient(circle at 25% 20%,#754331,#2B1B15 38%,#080505 88%)!important;box-shadow:inset -17px -18px 36px #080506,0 0 24px rgba(210,58,0,.20)!important;animation:wr-float 7s ease-in-out infinite!important;transition:transform .3s,border-color .3s,box-shadow .3s!important}
.st-key-universe .st-key-planet_analytics button{animation-delay:-1.5s!important}
.st-key-universe .st-key-planet_lab button{animation-delay:-3.2s!important}
.st-key-universe .st-key-planet_discover button{animation-delay:-4s!important}
.st-key-universe .st-key-planet_fire button{
 animation-delay:-5s!important;overflow:visible!important;
 background:radial-gradient(circle at 29% 20%,#FFB979 0%,#F47830 22%,#D23A00 49%,#7A220A 76%,#270A06 100%)!important;
 box-shadow:inset -12px -15px 28px rgba(30,5,2,.58),
 0 0 26px rgba(247,104,38,.42),0 0 58px rgba(210,58,0,.30),
 0 0 110px rgba(210,58,0,.13)!important;
 background-clip:padding-box!important;
}
.st-key-universe [class*="st-key-planet_"] button:hover{transform:scale(1.12)!important;border-color:#FFA46D!important;box-shadow:0 0 32px rgba(255,124,44,.7),0 0 80px rgba(210,58,0,.4),inset -13px -14px 30px #170A05!important}
.st-key-universe [class*="st-key-planet_"] button:focus-visible{outline:3px solid #FEFFFA!important;outline-offset:4px!important}
.wr-universe-tip{text-align:center;font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:#998B85;margin:7px 0 32px}
.wr-universe-tip strong{color:#F18457}
.wr-page-hero{padding:48px 0 26px;border-bottom:1px solid rgba(254,255,250,.12);margin-bottom:12px;position:relative;overflow:hidden}
.wr-page-hero:after{content:"";position:absolute;right:0;top:-90px;width:360px;height:280px;background:radial-gradient(ellipse,rgba(210,58,0,.21),transparent 70%);filter:blur(12px);pointer-events:none}
.wr-page-no{font-size:10px;color:#ED784C;letter-spacing:.22em;font-weight:800;margin-bottom:12px}
.wr-page-title{font-size:clamp(45px,5.8vw,79px);line-height:1.03;letter-spacing:-.07em;font-weight:500;margin:0!important;color:#FEFFFA}
.wr-page-title em{font-family:'Playfair Display',Georgia,serif;color:#D23A00;font-weight:400}
.wr-page-sub{font-size:14px;color:#AFA29A;max-width:630px;margin:18px 0 10px;line-height:1.75}
[data-testid="stAppViewContainer"]::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(ellipse 32% 35% at 6% 18%,rgba(143,36,7,.16),transparent),radial-gradient(ellipse 42% 45% at 99% 76%,rgba(210,58,0,.08),transparent);animation:wr-liquid 19s ease-in-out infinite alternate;filter:blur(27px)}
[data-testid="stMain"]{position:relative;z-index:1}
@keyframes wr-arrive{from{opacity:0;transform:translateY(21px);filter:blur(7px)}to{opacity:1;transform:translateY(0);filter:blur(0)}}
@keyframes wr-float{0%,100%{filter:brightness(1)}50%{filter:brightness(1.22)}}
@keyframes wr-breathe{0%,100%{filter:brightness(1)}50%{filter:brightness(1.16)}}
@keyframes wr-ring{0%,100%{transform:rotate(-27deg)}50%{transform:rotate(-24deg) skewY(3deg)}}
@keyframes wr-liquid{0%{transform:translate(-2%,1%) scale(1)}50%{transform:translate(4%,-5%) scale(1.12)}100%{transform:translate(-1%,5%) scale(1.07)}}
@media(max-width:850px){
 .st-key-universe{padding:12px 8px!important}
 .st-key-universe [class*="st-key-planet_"] button{height:105px!important;width:105px!important;min-height:105px!important;min-width:105px!important;font-size:10px!important}
 .wr-sun{height:145px;width:145px}.wr-sun-shell{height:175px}
 .st-key-solar_row_top{min-height:103px}.st-key-solar_row_middle{min-height:177px}.st-key-solar_row_bottom{min-height:104px}
}
@media(max-width:610px){
 .wr-space-head{margin:20px auto 15px}.wr-space-title{font-size:clamp(41px,9vw,65px)!important}.wr-space-sub{font-size:12px}
 .st-key-app_nav [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:3px!important}
 .st-key-app_nav button{font-size:9px!important;min-height:34px!important}
 .st-key-universe{margin-top:15px!important;padding:8px 0!important}
 .st-key-universe [data-testid="stHorizontalBlock"]{flex-direction:row!important;flex-wrap:nowrap!important;gap:3px!important}
 .st-key-universe [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important;width:33.33%!important}
 .st-key-universe [class*="st-key-planet_"] button{height:86px!important;width:86px!important;min-height:86px!important;min-width:86px!important;padding:5px!important;font-size:9px!important}
 .wr-sun{height:88px;width:88px}.wr-sun::before{border-width:4px}
 .wr-sun-inner{font-size:7px;letter-spacing:.04em}.wr-sun-inner span{font-size:5px}.wr-sun-shell{height:116px}
 .st-key-solar_row_top{min-height:94px}.st-key-solar_row_middle{min-height:120px}.st-key-solar_row_bottom{min-height:98px}
 .st-key-universe::before{height:235px}.st-key-universe::after{height:165px}
}
@media(prefers-reduced-motion:reduce){.st-key-universe button,.wr-sun,.wr-sun::before,[data-testid="stAppViewContainer"]::before{animation:none!important}}
</style>""", unsafe_allow_html=True)


def home_brand() -> None:
    st.markdown(
        '<div class="wr-homebrand"><span class="wr-mark"></span>'
        'WealthRank<b>.</b><small>INTERACTIVE FINANCIAL UNIVERSE</small></div>',
        unsafe_allow_html=True,
    )


def top_navigation() -> None:
    page = current_page()
    with st.container(key="app_nav"):
        columns = st.columns([2.1, .85, .85, 1.15, .95, .9], gap="small", vertical_alignment="center")
        with columns[0]:
            st.markdown(
                '<div class="wr-sitebar"><div class="wr-mark"></div>'
                '<div class="wr-sitebrand">WealthRank<b>.</b><small>WEALTH IN MOTION</small></div></div>',
                unsafe_allow_html=True,
            )
        for col, (slug, label) in zip(columns[1:], (
            ("portfolio", "Portfolio"), ("analytics", "Analytics"),
            ("discover", "Discover"), ("fire", "FIRE"), ("lab", "Model Lab"),
        )):
            with col:
                st.button(label, key="nav_" + slug,
                          type="primary" if page == slug else "secondary",
                          on_click=navigate, args=(slug,), use_container_width=True)


def page_header(number: str, title: str, subtitle: str) -> None:
    st.markdown(
        '<div class="wr-page-hero">'
        f'<div class="wr-page-no">{number} / WEALTHRANK EXPERIENCE</div>'
        f'<h1 class="wr-page-title">{title}</h1>'
        f'<p class="wr-page-sub">{subtitle}</p>'
        '</div>', unsafe_allow_html=True,
    )


def universe() -> None:
    st.markdown(
        '<div class="wr-space-head"><div class="wr-space-overline">'
        'TECHNOLOGY CRAFTED FOR ALL. NOT MACHINES.</div>'
        '<h1 class="wr-space-title">Wealth, in <em>orbit.</em></h1>'
        '<p class="wr-space-sub">One universe. Five independent experiences. '
        'Choose a planet to open its own financial workspace.</p></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="universe"):
        st.markdown('<div class="wr-starfield" aria-hidden="true"></div>',
                    unsafe_allow_html=True)
        with st.container(key="solar_row_top"):
            left, _, right = st.columns([1, 1, 1], gap="small", vertical_alignment="center")
            with left:
                with st.container(key="planet_portfolio"):
                    st.button("Portfolio", key="orbit_portfolio",
                              on_click=navigate, args=("portfolio",),
                              help="Holdings and net worth")
            with right:
                with st.container(key="planet_analytics"):
                    st.button("Analytics", key="orbit_analytics",
                              on_click=navigate, args=("analytics",),
                              help="Stock alpha, beta and returns")
        with st.container(key="solar_row_middle"):
            left, center, right = st.columns([1, 1, 1], gap="small", vertical_alignment="center")
            with left:
                with st.container(key="planet_lab"):
                    st.button("Model Lab", key="orbit_lab",
                              on_click=navigate, args=("lab",),
                              help="Model evaluation")
            with center:
                st.markdown(
                    '<div class="wr-sun-shell"><div class="wr-sun" aria-hidden="true">'
                    '<div class="wr-sun-inner">WEALTHRANK<span>FINANCIAL UNIVERSE</span>'
                    '</div></div></div>', unsafe_allow_html=True,
                )
            with right:
                with st.container(key="planet_discover"):
                    st.button("Discover", key="orbit_discover",
                              on_click=navigate, args=("discover",),
                              help="Up to ten ranked stock ideas")
        with st.container(key="solar_row_bottom"):
            _, center, _ = st.columns([1, 1, 1], gap="small", vertical_alignment="center")
            with center:
                with st.container(key="planet_fire"):
                    st.button("FIRE", key="orbit_fire",
                              on_click=navigate, args=("fire",),
                              help="Retirement projection calculator")
    st.markdown(
        '<div class="wr-universe-tip">HOVER TO HIGHLIGHT · '
        '<strong>CLICK A PLANET TO EXPLORE</strong></div>',
        unsafe_allow_html=True,
    )


def home_return() -> None:
    st.button("← Back to the universe", key="return_to_universe",
              on_click=navigate, args=("home",))
