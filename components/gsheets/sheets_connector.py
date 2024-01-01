import pandas as pd
import streamlit as st

from streamlit_gsheets import GSheetsConnection
from datetime import timezone, timedelta


# АБСТРАКТНЫЙ КЛАСС ДЛЯ РЕАЛИЗАЦИИ КОННЕКШЕНА К ГУГЛ ШИТС