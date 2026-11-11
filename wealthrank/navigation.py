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
/* New navigational system: one active experience per screen */
.wr-sitebar{display:flex;align-items:center;gap:10px;padding:6px 0}
.wr-sitebrand{font-size:24px;font-weight:800;letter-spacing:-.075em;color:#FEFFFA;white-space:nowrap}
.wr-sitebrand b{color:#D23A00}.wr-sitebrand small{font-size:9px;letter-spacing:.16em;color:#8E817C;display:block;font-weight:600}
.st-key-app_nav{padding:10px 0 19px;border-bottom:1px solid rgba(254,255,250,.12);margin-bottom:8px}
.st-key-app_nav button{min-height:41px!important;font-size:11px!important;letter-spacing:.01em!important;font-weight:700!important;padding:6px 8px!important}
.st-key-app_nav button[kind="primary"]{box-shadow:0 0 24px rgba(210,58,0,.22)!important}
.wr-active-tag{font-size:10px;text-transform:uppercase;color:#B0A39C;letter-spacing:.16em;white-space:nowrap}
.wr-space-head{max-width:1200px;margin:30px auto 0;text-align:center;position:relative;z-index:2}
.wr-space-overline{font-size:11px;font-weight:800;letter-spacing:.22em;color:#E5724D;text-transform:uppercase;animation:wr-arrive .8s ease both}
.wr-space-title{font-size:clamp(50px,7.8vw,112px);line-height:.96;font-weight:500;letter-spacing:-.075em;margin:18px 0 18px!important;color:#FEFFFA;animation:wr-arrive 1s ease both}
.wr-space-title em{font-family:'Playfair Display',Georgia,serif;font-weight:400;color:#D23A00}
.wr-space-sub{font-size:14px;line-height:1.7;color:rgba(254,255,250,.63);max-width:640px;margin:0 auto;animation:wr-arrive 1.2s ease both}
.st-key-universe{position:relative!important;height:640px;min-height:640px;max-width:1140px;margin:0 auto 12px!important;
 isolation:isolate;overflow:visible!important;background:radial-gradient(ellipse 41% 45% at 50% 52%,rgba(210,58,0,.12),transparent 85%)}
.st-key-universe::before,.st-key-universe::after{
 content:'';position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-20deg);
 border:1px solid rgba(254,255,250,.13);border-radius:50%;pointer-events:none;z-index:0}
.st-key-universe::before{width:min(88%,1000px);height:470px;box-shadow:inset 0 0 80px rgba(210,58,0,.018)}
.st-key-universe::after{width:min(70%,780px);height:345px;border-color:rgba(210,58,0,.23);transform:translate(-50%,-50%) rotate(31deg)}
.wr-starfield{position:absolute;inset:0;pointer-events:none;background-image:
 radial-gradient(circle at 4% 20%,#FEFFFA 1px,transparent 2px),radial-gradient(circle at 86% 12%,#FEFFFA 1px,transparent 2px),
 radial-gradient(circle at 25% 65%,#D23A00 1px,transparent 3px),radial-gradient(circle at 72% 76%,#FEFFFA 1px,transparent 2px),
 radial-gradient(circle at 51% 8%,#FEFFFA 1px,transparent 2px),radial-gradient(circle at 94% 55%,#D23A00 2px,transparent 3px);
 opacity:.46;filter:drop-shadow(0 0 4px #D23A00)}
.wr-star{position:absolute;width:270px;height:270px;left:50%;top:50%;transform:translate(-50%,-50%);
 border-radius:50%;z-index:1;pointer-events:none;background:
 radial-gradient(circle at 27% 23%,#FFD1A7 0%,#FF813B 8%,#DC4307 26%,#8F2407 48%,#240B07 75%,#080404 100%);
 box-shadow:0 0 35px rgba(236,80,12,.55),0 0 125px rgba(210,58,0,.19),
 inset -33px -43px 64px rgba(0,0,0,.76);animation:wr-breathe 9s ease-in-out infinite}
.wr-star:before{content:'';position:absolute;inset:23% -29%;border:10px solid #FF671B;border-radius:50%;transform:rotate(-34deg);
 box-shadow:0 0 22px rgba(255,103,27,.9),0 0 80px rgba(210,58,0,.48),inset 0 0 12px #D23A00;
 animation:wr-ring 10s ease-in-out infinite}
.wr-star-inner{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;
 font-size:13px;letter-spacing:.21em;font-weight:800;color:#FEFFFA;text-shadow:0 3px 14px #140500;z-index:2}
.wr-star-inner span{font-size:10px;color:rgba(254,255,250,.7);margin-top:7px;letter-spacing:.13em}
.st-key-universe .st-key-planet_portfolio,
.st-key-universe .st-key-planet_analytics,
.st-key-universe .st-key-planet_discover,
.st-key-universe .st-key-planet_fire,
.st-key-universe .st-key-planet_lab{
 position:absolute!important;z-index:5;min-width:0!important;max-width:none!important;background:none!important;
 overflow:visible!important;animation:wr-float 7s ease-in-out infinite;isolation:isolate}
.st-key-planet_portfolio{left:8%;top:8%}
.st-key-planet_analytics{right:12%;top:4%;animation-delay:-2.7s!important}
.st-key-planet_discover{right:2%;top:48%;animation-delay:-4.5s!important}
.st-key-planet_fire{right:25%;bottom:3%;animation-delay:-1.8s!important}
.st-key-planet_lab{left:11%;bottom:12%;animation-delay:-3.2s!important}
.st-key-universe [class*="st-key-planet_"] button{
 width:146px!important;height:146px!important;border-radius:50%!important;
 display:flex!important;align-items:center!important;justify-content:center!important;text-align:center!important;
 color:#FEFFFA!important;background:radial-gradient(circle at 25% 18%,#68473A 0%,#251814 28%,#100B09 72%,#050405 100%)!important;
 box-shadow:inset -20px -15px 40px rgba(0,0,0,.85),0 0 28px rgba(210,58,0,.16),0 0 2px rgba(254,255,250,.2)!important;
 border:1px solid rgba(254,255,250,.38)!important;
 font-size:13px!important;font-weight:800!important;letter-spacing:.015em!important;
 white-space:normal!important;line-height:1.4!important;transform:scale(1)!important;
 transition:transform .4s cubic-bezier(.16,1.4,.4,1),box-shadow .5s,border-color .5s,background .5s!important;
 position:relative;z-index:5;cursor:pointer!important;animation:none!important}
.st-key-planet_portfolio button{width:162px!important;height:162px!important}
.st-key-planet_discover button{width:160px!important;height:160px!important}
.st-key-planet_fire button{background:radial-gradient(circle at 23% 22%,#FA8745,#A72F07 27%,#31100A 63%,#080404)!important}
.st-key-planet_lab button{width:130px!important;height:130px!important}
.st-key-universe [class*="st-key-planet_"] button:hover{
 transform:scale(1.17)!important;border-color:#FF8A50!important;
 box-shadow:0 0 26px rgba(255,110,40,.6),0 0 83px rgba(210,58,0,.35),
 inset -18px -18px 40px rgba(0,0,0,.64)!important;
 background:radial-gradient(circle at 25% 20%,#ED7A42,#842B16 40%,#140908 85%)!important}
.st-key-universe [class*="st-key-planet_"] button:focus-visible{outline:3px solid #FEFFFA!important;outline-offset:4px!important}
.wr-universe-tip{font-size:11px;text-align:center;letter-spacing:.12em;text-transform:uppercase;color:#9B8A82;margin:2px 0 40px;animation:wr-arrive 1.4s ease both}
.wr-universe-tip strong{color:#E9764E}
.wr-page-hero{padding:48px 0 26px;border-bottom:1px solid rgba(254,255,250,.12);margin-bottom:12px;position:relative;overflow:hidden}
.wr-page-hero:after{content:'';position:absolute;right:0;top:-90px;width:360px;height:280px;
 background:radial-gradient(ellipse,rgba(210,58,0,.21),transparent 70%);filter:blur(12px);pointer-events:none}
.wr-page-no{font-size:10px;color:#ED784C;letter-spacing:.22em;font-weight:800;margin-bottom:12px}
.wr-page-title{font-size:clamp(45px,5.8vw,79px);line-height:1.03;letter-spacing:-.07em;font-weight:500;margin:0!important;color:#FEFFFA}
.wr-page-title em{font-family:'Playfair Display',Georgia,serif;color:#D23A00;font-weight:400}
.wr-page-sub{font-size:14px;color:#AFA29A;max-width:630px;margin:18px 0 10px;line-height:1.75}
[data-testid="stAppViewContainer"]::before{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
 background:radial-gradient(ellipse 32% 35% at 6% 18%,rgba(143,36,7,.16),transparent),
 radial-gradient(ellipse 42% 45% at 99% 76%,rgba(210,58,0,.08),transparent);
 animation:wr-liquid 19s ease-in-out infinite alternate;filter:blur(27px)}
[data-testid="stMain"]{position:relative;z-index:1}
@keyframes wr-arrive{from{opacity:0;transform:translateY(21px);filter:blur(7px)}to{opacity:1;transform:translateY(0);filter:blur(0)}}
@keyframes wr-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
@keyframes wr-breathe{0%,100%{filter:brightness(1)}50%{filter:brightness(1.17)}}
@keyframes wr-ring{0%,100%{transform:rotate(-34deg)}50%{transform:rotate(-29deg) skewY(4deg)}}
@keyframes wr-liquid{0%{transform:translate(-2%,1%) scale(1)}50%{transform:translate(4%,-5%) scale(1.12)}100%{transform:translate(-1%,5%) scale(1.07)}}
@media(max-width:900px){
 .st-key-app_nav button{font-size:10px!important}
 .st-key-universe{height:580px;min-height:580px}
 .st-key-universe [class*="st-key-planet_"] button{width:123px!important;height:123px!important;font-size:11px!important}
 .st-key-planet_portfolio{left:1%}.st-key-planet_discover{right:0%}.st-key-planet_lab{left:3%}
 .wr-star{width:216px;height:216px}
}
@media(max-width:610px){
 .wr-space-head{margin-top:24px}.wr-space-title{font-size:clamp(53px,12vw,78px)}
 .wr-space-sub{font-size:12px}
 .st-key-app_nav [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:3px!important}
 .st-key-app_nav button{min-height:36px!important;font-size:9px!important;padding:5px!important}
 .st-key-universe{height:490px;min-height:490px;margin-bottom:0!important}
 .st-key-universe::before{height:300px;width:97%}
 .st-key-universe::after{height:230px;width:79%}
 .wr-star{width:153px;height:153px}
 .wr-star:before{border-width:6px}
 .wr-star-inner{font-size:10px}.wr-star-inner span{font-size:8px}
 .st-key-universe [class*="st-key-planet_"] button{width:94px!important;height:94px!important;font-size:10px!important}
 .st-key-planet_portfolio{left:0%;top:8%}
 .st-key-planet_analytics{right:0%;top:6%}
 .st-key-planet_discover{right:0%;top:53%}
 .st-key-planet_fire{right:22%;bottom:0%}
 .st-key-planet_lab{left:1%;bottom:9%}
 .wr-universe-tip{margin-bottom:22px}
}
@media(prefers-reduced-motion:reduce){
 .st-key-universe [class*="st-key-planet_"],.wr-star,.wr-star:before,
 [data-testid="stAppViewContainer"]::before{animation:none!important}
}
</style>""", unsafe_allow_html=True)


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
        '<div class="wr-space-head">'
        '<div class="wr-space-overline">TECHNOLOGY CRAFTED FOR ALL. NOT MACHINES.</div>'
        '<h1 class="wr-space-title">Wealth, in <em>orbit.</em></h1>'
        '<p class="wr-space-sub">One universe. Five independent experiences. '
        'Choose a planet to understand your portfolio, explore new ideas or plot your financial independence.</p>'
        '</div>', unsafe_allow_html=True,
    )
    with st.container(key="universe"):
        st.markdown(
            '<div class="wr-starfield"></div><div class="wr-star">'
            '<div class="wr-star-inner">WEALTHRANK<span>YOUR CENTER OF GRAVITY</span></div>'
            '</div>', unsafe_allow_html=True,
        )
        choices = [
            ("portfolio", "01 · Portfolio", "Import, holdings and net worth"),
            ("analytics", "02 · Analytics", "Alpha, beta, returns and charts"),
            ("discover", "03 · Discover", "Top 10 ranked ideas"),
            ("fire", "04 · FIRE", "Plan your freedom"),
            ("lab", "05 · Model Lab", "Evaluation and experiments"),
        ]
        for slug, label, help_text in choices:
            with st.container(key="planet_" + slug):
                st.button(label, key="orbit_" + slug, help=help_text,
                          on_click=navigate, args=(slug,))
    st.markdown(
        '<div class="wr-universe-tip">↖ <strong>HOVER</strong> TO HIGHLIGHT · '
        '<strong>CLICK</strong> A PLANET TO EXPLORE</div>',
        unsafe_allow_html=True,
    )


def home_return() -> None:
    st.button("← Back to the universe", key="return_to_universe",
              on_click=navigate, args=("home",))
