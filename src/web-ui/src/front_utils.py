import base64
import html
import hashlib
import streamlit as st


# Получаем аватар
def get_avatar(seed):
    return f"https://api.dicebear.com/8.x/initials/svg?seed={seed}"


def avatar_for(name):
    return get_avatar(name)


# Для бейджа с уверенностью
def confidence_badge(val):
    val = float(val)  # 0..1
    pct = val * 100
    if val >= 0.7:
        bg = "#2ecc71"  # зелёная
    elif val >= 0.5:
        bg = "#f1c40f"  # жёлтая
    else:
        bg = "#bdc3c7"  # серая
    st.markdown(
        f'<span class="conf-badge" style="background:{bg}">Уверенность: {pct:.1f}%</span>',
        unsafe_allow_html=True,
    )


# Для JS внутри e-mail view
def html_id(key: str) -> str:
    return hashlib.md5(key.encode("utf-8")).hexdigest()


# Для отображения шаблона e-mail
def email_view_with_copy(email: str, key: str):
    btn_id = html_id("btn_" + key)
    st_id = html_id("st_" + key)

    b64 = base64.b64encode(email.encode("utf-8")).decode("ascii")
    escaped_email = html.escape(email)

    st.iframe(
        f"""
    <div style="
        box-sizing:border-box;
        height:100%;
        background:#f6f8fc;
        font-family:Roboto, Arial, sans-serif;
        padding:12px;
    ">
      <div style="
          height:100%;
          background:#fff;
          border:1px solid #dadce0;
          border-radius:16px;
          overflow:hidden;
          display:flex;
          flex-direction:column;
      ">
        <div style="
            padding:14px 16px 12px 16px;
            border-bottom:1px solid #e8eaed;
        ">
          <div style="
              font-size:20px;
              line-height:1.3;
              font-weight:400;
              color:#202124;
              letter-spacing:0;
              margin:0 0 10px 0;
              white-space:nowrap;
              overflow:hidden;
              text-overflow:ellipsis;
          ">
            {'Шаблон письма'}
          </div>
        </div>

        <div style="
            flex:1;
            min-height:0;
            overflow:auto;
            padding:20px 16px 18px 16px;
            color:#202124;
            font-size:14px;
            line-height:1.7;
            letter-spacing:0;
            white-space:normal;
            word-break:break-word;
            text-rendering:optimizeLegibility;
            -webkit-font-smoothing:antialiased;
            -moz-osx-font-smoothing:grayscale;
        ">
          {escaped_email}
        </div>

        <div style="
            padding:12px 16px;
            border-top:1px solid #e8eaed;
            display:flex;
            align-items:center;
            gap:10px;
            background:#fff;
        ">
          <button id="{btn_id}" style="
              height:32px;
              padding:0 14px;
              border:1px solid #dadce0;
              border-radius:16px;
              background:#fff;
              color:#3c4043;
              cursor:pointer;
              font-family:Roboto, Arial, sans-serif;
              font-size:13px;
              font-weight:500;
              letter-spacing:0;
          ">
            Копировать
          </button>
          <span id="{st_id}" style="
              color:#5f6368;
              font-size:12px;
              line-height:1.4;
          "></span>
        </div>
      </div>

      <script>
        const b64 = "{b64}";
        const btn = document.getElementById("{btn_id}");
        const st  = document.getElementById("{st_id}");

        btn.addEventListener("click", async () => {{
          const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
          const text = new TextDecoder("utf-8").decode(bytes);

          await navigator.clipboard.writeText(text);
          st.textContent = "Скопировано!";
          setTimeout(() => {{ st.textContent = ""; }}, 1200);
        }});
      </script>
    </div>
    """,
        height=340,
    )


def badge_html(name, topic, bg="#dbeafe", fg="#0f172a", br="#2563eb", n_bg="#2563eb"):
    st.markdown(
        f"""
        <span style="display:inline-flex;
            align-items:center;
            display:inline-flex;
            padding:0.35rem 0.7rem;">
        <span style="
            padding:0.35rem 0.7rem;
            border:1px solid {br};
            border-radius:999px;
            background:linear-gradient(180deg, {bg} 0%, #ffffff 100%);
            color:{fg};
            font-weight:700;
            font-size:0.92rem;
            line-height:1;
            box-shadow:0 1px 2px rgba(15, 23, 42, 0.12);
            vertical-align:middle;
            white-space:nowrap;">
            {html.escape(topic)}
        </span>
        <span style="visibility:hidden;">text</span>
        {html.escape(name)}
        </span>
        """,
        unsafe_allow_html=True,
    )
