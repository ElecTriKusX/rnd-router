import streamlit as st
import uuid

from front_utils import avatar_for, badge_html, confidence_badge, email_view_with_copy
from mocks import decompose, draft_email, rerank, retrieve


#Стили/Внешний вид
st.logo(r"src\logo.png", size='large')
st.set_page_config(layout="wide")
st.set_page_config(
    page_title="R&D",
    page_icon="🔎",
)


#Для шапки страницы
st.markdown(
    """
    <style>
    .stAppHeader {
        background-color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


#Для бейджей с уверенностью
st.markdown(
    """
<style>
.conf-badge{
  display:inline-block;
  padding:6px 10px;
  border-radius:8px;
  font-weight:700;
  color:#111;
}
</style>
""",
    unsafe_allow_html=True,
)


def show_cards(subtask, top5, query=""):
    st.subheader(f"Кандидаты: {subtask.name}")
    st.space()
    for row_start in range(0, len(top5), 3):
        row_items = top5[row_start:row_start + 3]
        cols = st.columns(3)
        for col, cd in zip(cols, row_items):
            with col:
                with st.container(border=True, height="stretch"):
                    inner_cols = st.columns([1, 6])
                    with inner_cols[0]:
                        st.image(avatar_for(cd.name), width=48)
                    with inner_cols[1]:
                        st.write(f"**ФИО:** {cd.name} <br> **Подразделение:** {cd.division}", unsafe_allow_html=True)

                    confidence_badge(cd.score)
                    st.write('\n'.join([f"- {rs}" for rs in cd.reasons]))

                    exp_key = uuid.uuid4().hex
                    copy_key = uuid.uuid4().hex
                    with st.expander("Развернуть", expanded=False, key=exp_key):
                        email = draft_email(query, cd)
                        email_view_with_copy(email, key=copy_key)


#Вкладки
default_tab, tab2, tab3 = st.tabs(
    ["Подбор", "...", "..."], on_change="rerun"
)


#Основная логика здесь...
if default_tab.open:
    with default_tab:
        st.write("Подбор кандидатов")
        query = st.text_area(
            "Текст запроса",
            placeholder="Пишите здесь...",
            width=400,
            height="content"
        )
        if st.button("Подобрать"):
            subtasks = decompose(query)
            st.subheader("Разложение на подзадачи:")
            st.space()
            for i, sb in enumerate(subtasks, start=1):
                badge_html(sb.name, sb.topic)
            st.space()
            for sb in subtasks:
                candidates = retrieve(sb.topic)
                top5 = rerank(sb, candidates)
                show_cards(sb, top5)


if tab2.open:
    with tab2:
        st.write("...")


if tab3.open:
    with tab3:
        st.write("...")
