import os
import shutil  # Pro mazání prázdné složky
import json

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.gridlayout import GridLayout
from deep_translator import GoogleTranslator
from kivy.uix.scrollview import ScrollView

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Konfigurace API klíče
api = os.getenv("API_KEY")
genai.configure(api_key=api)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

SETTINGS_FILE = os.path.join(".\\LanguageApp", "settings.json")

def load_settings():
    """Načte nastavení ze souboru settings.json nebo vrátí výchozí nastavení, pokud je soubor prázdný nebo neexistuje."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data if data else {"font_size": 14}  # Výchozí hodnota, pokud je soubor prázdný
            except json.JSONDecodeError:
                return {"font_size": 14}  # Výchozí hodnota, pokud je soubor neplatný
    else:
        return {"font_size": 14}  # Výchozí nastavení


def save_settings(settings):
    """Uloží nastavení do souboru settings.json."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

class MainBox(BoxLayout):
    def __init__(self, **kwargs):
        super(MainBox, self).__init__(**kwargs)
        # Načte nastavení
        self.settings = load_settings()

        # Nastaví velikost písma na základě načteného nastavení
        self.font_size = self.settings.get("font_size", 14)
        
        # Použije velikost písma na příslušné prvky
        self.apply_font_size()

        self.language_button = self.ids.language_button
        self.language_button.text = "GER"  # Výchozí jazyk

        self.level_button = self.ids.level_button
        self.level_button.text = "B1"  # Výchozí úroveň
    def apply_font_size(self):
        """Nastaví velikost písma na odpovídající prvky."""
        self.ids.language_button.font_size = self.font_size
        self.ids.level_button.font_size = self.font_size
        self.ids.word_input.font_size = self.font_size
        self.ids.result_label.font_size = self.font_size
        # Přidejte zde další prvky, které chcete přizpůsobit velikosti písma
    def open_settings(self):
        """Otevře popup okno pro nastavení velikosti písma."""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Popisek pro posuvník
        label = Label(text="Velikost písma", size_hint_y=None, height=30)
        layout.add_widget(label)

        # Posuvník pro nastavení velikosti písma
        slider = Slider(min=10, max=30, value=self.font_size, size_hint_y=None, height=44)
        layout.add_widget(slider)

        # Tlačítko pro potvrzení změn
        btn_confirm = Button(text="Potvrdit", size_hint_y=None, height=44)
        btn_confirm.bind(on_release=lambda *args: self.set_font_size(slider.value))
        layout.add_widget(btn_confirm)

        # Vytvoří a otevře popup okno
        self.settings_popup = Popup(
            title="Nastavení",
            content=layout,
            size_hint=(0.6, 0.4),
            auto_dismiss=True
        )
        self.settings_popup.open()

    def set_font_size(self, new_size):
        """Nastaví novou velikost písma, uloží ji a aktualizuje zobrazení."""
        self.font_size = int(new_size)
        self.settings["font_size"] = self.font_size
        save_settings(self.settings)  # Uloží nastavení do JSON souboru

        # Aktualizuje velikost písma v prvcích a zavře popup
        self.apply_font_size()
        self.settings_popup.dismiss()

    def open_language_selection(self):
        """Otevře modální okno s výběrem jazyků uprostřed obrazovky."""
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        for lang in ["CZ", "ENG", "GER"]:
            btn = Button(text=lang, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: self.select_language(btn.text))
            layout.add_widget(btn)

        self.popup = Popup(
            title="Vyberte jazyk",
            content=layout,
            size_hint=(0.6, 0.4),
            auto_dismiss=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}  # Středové umístění
        )
        self.popup.open()

    def select_language(self, language):
        """Nastaví vybraný jazyk na tlačítko a zavře nabídku."""
        self.language_button.text = language
        self.popup.dismiss()

    def open_level_selection(self):
        """Otevře modální okno s výběrem jazykové úrovně uprostřed obrazovky, s kategoriemi nad možnostmi."""
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        levels = {
            "Základní": ["A1", "A2"],
            "Pokročilá": ["B1", "B2"],
            "Super": ["C1", "C2"]
        }

        # Přidáme popisky kategorií a jejich úrovně
        for category, levels_list in levels.items():
            # Název kategorie jako Label
            layout.add_widget(Label(text=category, size_hint_y=None, height=30, halign="center", valign="middle"))

            # Tlačítka pro každou úroveň v kategorii
            for level in levels_list:
                btn = Button(text=level, size_hint_y=None, height=44, text_size=(None, None))  # Text zalomen
                btn.bind(on_release=lambda btn: self.select_level(btn.text))
                layout.add_widget(btn)

        self.popup_level = Popup(
            title="Vyberte jazykovou úroveň",
            content=layout,
            size_hint=(0.6, 0.6),
            auto_dismiss=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}  # Středové umístění
        )
        self.popup_level.open()

    def select_level(self, level):
        """Nastaví vybranou úroveň na tlačítko a zavře nabídku."""
        self.level_button.text = level
        self.popup_level.dismiss()

    def generate_sentence(self):
        word = self.word_input.text
        if word:
            prompt = (
                f"Napiš 5 krátkých vět v {self.language_button.text} na úrovni {self.level_button.text}, která obsahuje slovo '{word}'. "
                "Věta by měla být jednoduchá a srozumitelná pro danou jazykovou úroveň."
                "Piš pouze věty, bez žádného úvodního slova. Žádné číslování ani jiné znaky"
            )
            response = model.generate_content(prompt)
            self.display_generated_sentences(response.text)
        else:
            self.result_label.text = 'Prosím zadejte slovo.'



    def display_generated_sentences(self, text):
        """Zobrazí generované věty a jejich překlady, včetně překladu zadaného slova."""
        self.result_layout.clear_widgets()  # Vyčistí předchozí výsledky
        sentences = text.strip().split("\n")  # Rozdělí text na jednotlivé věty

        # Odstraní prázdné řádky
        sentences = [s for s in sentences if s.strip()]  # Zůstávají pouze neprázdné věty

        # Přidáme zadané slovo na konec seznamu vět
        word = self.word_input.text
        if word:
            sentences.append(word)

        # Iniciujeme překladač
        source_lang = 'de' if self.language_button.text == "GER" else 'en' if self.language_button.text == "ENG" else 'cs'
        translator = GoogleTranslator(source=source_lang, target='cs')

        # Přeložíme věty včetně zadaného slova
        combined_sentences = "\n".join(sentences)
        translations = translator.translate(combined_sentences)

        # Rozdělíme překlady podle oddělovače
        translated_sentences = translations.split("\n")

        # Nastavíme překlad zadaného slova do labelu 'result_label'
        self.result_label.text = translated_sentences[-1]

        # Zobrazíme originální a přeložené věty
        for i in range(len(sentences) - 1):  # Pro každou větu kromě poslední
            row_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44)
            
            combined_text = f"{sentences[i]}\n{translated_sentences[i]}"
            sentence_label = Label(text=combined_text, size_hint_x=1, halign='left', valign='middle', text_size=(None, None))

            button = Button(text='Uložit', size_hint_x=0.2)
            button.bind(on_release=lambda btn, sent=combined_text: self.save_sentence(sent))

            row_layout.add_widget(sentence_label)
            row_layout.add_widget(button)
            self.result_layout.add_widget(row_layout)

    def save_sentence(self, sentence):
        """Uloží větu do složky s názvem zadaného slova."""
        word = self.word_input.text.strip()  # Získá zadané slovo a odstraní mezery na začátku a na konci
        if not word:
            print("Slovo nebylo zadáno.")
            return

        # Vytvoří hlavní složku, pokud neexistuje
        folder_path = os.path.join(".\\LanguageApp\\savedWords")
        os.makedirs(folder_path, exist_ok=True)

        # Definování cesty k souboru na základě slova
        file_path = os.path.join(folder_path, f"{word}.txt")

        # Otevře existující soubor nebo vytvoří nový, pokud neexistuje, a zapíše větu
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(sentence + "\n\n")  # Každou větu oddělí prázdným řádkem

        print(f"Uložená věta: {sentence}")

    def show_saved_sentences(self):
        """Zobrazí seznam složek se slovy a umožní vyhledávání podle názvu složky."""
        
        # Cesta ke složce s uloženými soubory
        folder_path = os.path.join(".\\LanguageApp\\savedWords")
        
        # Zkontroluje, zda složka existuje a obsahuje nějaké soubory
        if not os.path.exists(folder_path) or not os.listdir(folder_path):
            content = Label(text="Žádné uložené věty.")
        else:
            # Layout pro zobrazení obsahu s vyhledáváním
            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            
            # Textové pole pro vyhledávání
            search_input = TextInput(hint_text="Vyhledat slovo", size_hint_y=None, height=44)
            search_input.bind(text=self.update_word_list)
            content.add_widget(search_input)
            
            # Layout pro zobrazení seznamu tlačítek s výsledky
            self.scroll_view = ScrollView(size_hint=(1, 1))
            self.word_layout = BoxLayout(orientation='vertical', size_hint_y=None)
            self.word_layout.bind(minimum_height=self.word_layout.setter('height'))
            self.scroll_view.add_widget(self.word_layout)
            content.add_widget(self.scroll_view)

            # Uloží seznam všech dostupných složek pro pozdější filtrování
            self.saved_words = [file_name[:-4] for file_name in os.listdir(folder_path) if file_name.endswith(".txt")]

            # Inicializace tlačítek pro všechna slova
            self.update_word_list(search_input)  # Zde předáváme search_input přímo

        # Zobrazí popup s vyhledávacím polem a seznamem tlačítek
        self.popup_saved = Popup(
            title="Uložené věty podle slov",
            content=content,
            size_hint=(0.8, 0.8),
            auto_dismiss=True
        )
        self.popup_saved.open()

    def update_word_list(self, instance, *args):
        """Aktualizuje zobrazený seznam tlačítek na základě vyhledávacího dotazu."""
        search_text = instance.text  # Načte aktuální text z TextInput
        self.word_layout.clear_widgets()  # Vymaže aktuální seznam tlačítek

        # Filtrovat slova podle vyhledávacího textu (ignoruje velikost písmen)
        filtered_words = [word for word in self.saved_words if search_text.lower() in word.lower()]

        # Vytvoří tlačítka pro každé filtrované slovo
        for word in filtered_words:
            btn = Button(text=word, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn, word=word: self.display_sentences(word))
            self.word_layout.add_widget(btn)

    def display_sentences(self, word):
        """Zobrazí věty uložené pro konkrétní slovo, včetně překladu, s možností smazat obě věty."""
        folder_path = os.path.join(".\\LanguageApp\\savedWords")
        file_path = os.path.join(folder_path, f"{word}.txt")

        # Načte věty ze souboru, pokud existuje
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sentences = f.read().strip().split("\n\n")  # Předpokládáme, že každá dvojice je oddělena prázdným řádkem
        except FileNotFoundError:
            sentences = ["Žádné uložené věty."]

        # Vytvoří layout pro popup s rolováním
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        scroll_view = ScrollView(size_hint=(1, 1))
        sentences_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        sentences_layout.bind(minimum_height=sentences_layout.setter('height'))

        # Vytvoří řádky pro každou dvojici vět s tlačítkem „Smazat“
        for combined_sentence in sentences:
            sentence_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
            
            # Label s kombinovaným textem (originál + překlad)
            sentence_label = Label(text=combined_sentence.strip(), size_hint_x=0.8, halign="left", valign="middle", text_size=(None, None))
            sentence_row.add_widget(sentence_label)

            # Tlačítko pro smazání dvojice vět
            delete_button = Button(text="Smazat", size_hint_x=0.2)
            delete_button.bind(on_release=lambda btn, sent=combined_sentence: self.delete_sentence(word, sent))
            sentence_row.add_widget(delete_button)

            sentences_layout.add_widget(sentence_row)

        scroll_view.add_widget(sentences_layout)
        layout.add_widget(scroll_view)

        # Zobrazí popup pro konkrétní slovo
        self.popup_sentences = Popup(
            title=f"Věty pro '{word}'",
            content=layout,
            size_hint=(0.8, 0.8),
            auto_dismiss=True
        )
        self.popup_sentences.open()

    def delete_sentence(self, word, sentence_to_delete):
        """Odstraní vybranou dvojici vět (originál + překlad) ze souboru pro konkrétní slovo.
        Pokud je soubor prázdný, smaže jej, a pokud složka zůstane prázdná, smaže i složku."""
        folder_path = os.path.join(".\\LanguageApp\\savedWords")
        file_path = os.path.join(folder_path, f"{word}.txt")

        # Načte všechny dvojice vět a odstraní vybranou dvojici
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sentences = f.read().strip().split("\n\n")  # Odděluje dvojice prázdnými řádky

            # Zapíše všechny věty kromě té, která má být smazána
            with open(file_path, "w", encoding="utf-8") as f:
                for sentence in sentences:
                    if sentence.strip() != sentence_to_delete.strip():
                        f.write(sentence + "\n\n")  # Každou dvojici odděluje prázdným řádkem

            print(f"Dvojice vět '{sentence_to_delete.strip()}' byla smazána.")
            
            # Zkontroluje, zda je soubor nyní prázdný
            if os.path.getsize(file_path) == 0:
                os.remove(file_path)  # Smaže prázdný soubor
                print(f"Soubor '{file_path}' byl smazán, protože je prázdný.")
                
                # Zkontroluje, zda je složka prázdná, a pokud ano, smaže ji
                if not os.listdir(folder_path):
                    shutil.rmtree(folder_path)  # Smaže prázdnou složku
                    print(f"Složka '{folder_path}' byla smazána, protože je prázdná.")

            # Obnoví zobrazení vět po smazání
            self.display_sentences(word)
            
        except FileNotFoundError:
            print("Soubor neexistuje, nelze smazat větu.")





class MyApp(App):
    def build(self):
        return MainBox()


if __name__ == '__main__':
    MyApp().run()