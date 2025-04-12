import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from animation_occ import start_animation
from function_occ import GCodeParser
import threading
import math

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("G-Code Generator")
        self.default_width = 265
        self.root.minsize(self.default_width, 0)
        self.nazwa_programu = ""
        self.is_program_saved = True
        self.program_data = []
        self.pre_width = 0
        self.pre_length = 0
        self.pre_height = 0
        self.workpiece_params = {}
        self.max_tool_radius = 20
        self.main_menu()

    def main_menu(self):
        self.clear_window()
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Wybierz program", font=("Arial", 16)).pack(pady=10, fill=tk.X)
        
        buttons = [
            ("Stwórz własny program", self.request_program_name),
            ("Wczytaj poprzedni program", self.load_existing_program)
        ]

        for text, cmd in buttons:
            tk.Button(main_frame, text=text, command=cmd).pack(pady=5, fill=tk.X, expand=True)

        self.root.after(50, self._update_window_min_size)

    def load_existing_program(self):
        path = filedialog.askopenfilename(
            filetypes=[("G-code files", "*.gcode"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, 'r') as f:
                self.program_data = [line.strip() for line in f.readlines()]
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd wczytywania pliku: {str(e)}")
            return

        self.request_program_name(is_new_program=False)
        
    def request_program_name(self, is_new_program=True):
        name = simpledialog.askstring("Nazwa programu", "Podaj nazwę programu:")
        if name and self.is_valid_name(name):
            self.nazwa_programu = name
            self.is_program_saved = False
            if is_new_program:
                self.program_data = []
            self.make_operation()
        elif name:
            messagebox.showerror("Błąd", "Nazwa zawiera niedozwolone znaki (spacje/tabulacje)")
                     
    def is_valid_name(self, name):
        return all(c not in name for c in [' ', '\t', '\n'])

    def make_operation(self):
        self.clear_window()
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text=f"Tworzenie programu: {self.nazwa_programu}", font=("Arial", 16)).pack(pady=10, fill=tk.X)

        buttons = [
            ("Zmień nazwę programu", self.change_program_name),
            ("Dodaj dane do programu", self.add_data_to_program),
            ("Animacja", self.input_pre),
            ("Powrót do menu głównego", self.confirm_exit_to_main_menu)
        ]

        for text, cmd in buttons:
            tk.Button(main_frame, text=text, command=cmd).pack(pady=5, fill=tk.X, expand=True)

        self.root.after(50, self._update_window_min_size)

    def reset_animation(self):
        if hasattr(self, 'animation_handler'):
            self.animation_handler.stop()
        self._remove_existing_workpiece()

    def on_start_animation_btn_clicked(self):
        try:
            self.reset_animation()
            if hasattr(self, 'workpiece_params'):
                self._init_workpiece(**self.workpiece_params)
            else:
                raise ValueError("Brak parametrów półfabrykatu. Zapisz je najpierw.")
            if not self.program_data:
                raise ValueError("Brak danych Gcode.")
            self.prepare_animation(self.program_data)
            self.start_animation()
        except Exception as e:
            print(f"Błąd: {e}")

    def input_pre(self):
        def on_save():
            try:
                self.pre_width = float(width_entry.get())
                self.pre_length = float(length_entry.get())
                self.pre_height = float(height_entry.get())
                if self.pre_width <= 0 or self.pre_length <= 0 or self.pre_height <= 0:
                    raise ValueError
                root.destroy()
                self.animation_menu()
            except:
                messagebox.showerror("Błąd", "Wprowadź poprawne wartości dodatnie")

        root = tk.Toplevel(self.root)
        root.title("Wymiary półfabrykatu")
        
        tk.Label(root, text="Szerokość:").grid(row=0, column=0, padx=5, pady=5)
        width_entry = tk.Entry(root)
        width_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(root, text="Długość:").grid(row=1, column=0, padx=5, pady=5)
        length_entry = tk.Entry(root)
        length_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(root, text="Wysokość:").grid(row=2, column=0, padx=5, pady=5)
        height_entry = tk.Entry(root)
        height_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Button(root, text="Zapisz", command=on_save).grid(row=3, column=0, padx=5, pady=10)
        tk.Button(root, text="Anuluj", command=root.destroy).grid(row=3, column=1, padx=5, pady=10)


    def animation_menu(self):
        self.clear_window()
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        tk.Button(main_frame, text="Zmień wymiary półfabrykatu", command=self.input_pre).pack(pady=5, fill=tk.X, expand=True)
        
        tk.Button(
            main_frame,
            text="Rozpocznij animację",
            command=lambda: threading.Thread(
                target=start_animation,
                args=(self.program_data, self.pre_width, self.pre_length, self.pre_height),
                daemon=True
            ).start()
        ).pack(pady=5, fill=tk.X, expand=True)
        
        tk.Button(main_frame, text="Powrót", command=self.make_operation).pack(pady=5, fill=tk.X, expand=True)

        self.root.after(50, self._update_window_min_size)

    def update_program_label(self):
        label = tk.Label(self.root, text=f"Tworzenie programu: {self.nazwa_programu}", font=("Arial", 16))
        label.pack(pady=10)

    def change_program_name(self):
        new_name = simpledialog.askstring("Zmiana nazwy", "Podaj nową nazwę programu:")
        if new_name and self.is_valid_name(new_name):
            self.nazwa_programu = new_name
            self.make_operation()
        elif new_name:
            messagebox.showerror("Błąd", "Niepoprawna nazwa programu")
            
    def add_data_to_program(self):
        self.submenu("Dodaj dane do programu")

    def submenu(self, title):
        self.clear_window()
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text=title, font=("Arial", 16)).pack(pady=10, fill=tk.X)

        buttons = [
            ("Zmień jednostki", self.units_submenu),
            ("Zmień narzędzie", self.change_tool_prompt),
            ("Włącz/Wyłącz chłodziwo", self.coolant_control_submenu),
            ("Zmiana Posuw (mm/min)", self.change_feed_prompt),
            ("Idź do (X/Y/Z)", self.go_to_submenu),
            ("Frezowanie do (X/Y/Z)", self.mill_to_submenu),
            ("Otwór", self.drill_material_submenu),
            ("Wwiercenie do materiału", self.bore_material_submenu),
            ("Frezowanie kieszeni/czoła", self.face_mill_submenu),
            ("Frezowanie kieszeni okrągłej", self.circular_pocket_submenu),
            ("Frezowanie po łuku lub okręgu", self.arc_mill_submenu),
            ("Zapisz program", self.save_file),
            ("Edytuj recznie", self.edit_by_hand),
            ("Pokaż czas obróbki", self.show_machining_time),
            ("Powrót", self.make_operation)
        ]

        for text, cmd in buttons:
            tk.Button(main_frame, text=text, command=cmd).pack(pady=2, fill=tk.X, expand=True)

        self.root.after(50, self._update_window_min_size)

    def edit_by_hand(self):
        editor = tk.Toplevel(self.root)
        editor.title("Edytor G-code")
        editor.geometry("600x400")
        
        text_area = tk.Text(editor, font=("Courier", 12))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.END, "\n".join(self.program_data))
        
        def save_and_close():
            self.program_data = text_area.get("1.0", tk.END).splitlines()
            self.is_program_saved = False
            editor.destroy()
        
        button_frame = tk.Frame(editor)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_frame, text="Zapisz", command=save_and_close).pack(side=tk.LEFT)
        tk.Button(button_frame, text="Anuluj", command=editor.destroy).pack(side=tk.RIGHT)

    def save_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".gcode",
            filetypes=[("G-code files", "*.gcode"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            try:
                with open(path, "w") as f:
                    f.write("\n".join(self.program_data))
                self.is_program_saved = True
                messagebox.showinfo("Sukces", "Plik zapisano pomyślnie")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać pliku: {str(e)}")
                
    def add_numbering(array):
        n = 5
        ret_arr = []
        for line in array:
            ret_arr.append(f"N{n} {line}")
            n += 5
        return ret_arr

    def arc_mill_clockwise(self, x, y, i, j, radius):
        commands = []
        x = round(x, 3)
        y = round(y, 3)
        i = round(i, 3)
        j = round(j, 3)
        radius = round(radius, 3)
        commands.append("M3")
        if i == 0 and j == 0:
            commands.append(f"G02 X{x} Y{y} R{radius}")
        else:
            commands.append(f"G02 X{x} Y{y} I{i} J{j}")
        commands.append("M5")
        return commands

    def arc_mill_counterclockwise(self, x, y, i, j, radius):
        commands = []
        x = round(x, 3)
        y = round(y, 3)
        i = round(i, 3)
        j = round(j, 3)
        radius = round(radius, 3)
        commands.append("M3")
        if i == 0 and j == 0:
            commands.append(f"G03 X{x} Y{y} R{radius}")
        else:
            commands.append(f"G03 X{x} Y{y} I{i} J{j}")
        commands.append("M5")
        return commands

    def circle_mill(self, x, y, radius):
        start_x = x - radius
        start_y = y - radius
        return [
            f"G01 X{round(start_x - radius, 3)} Y{round(start_y, 3)}",
            f"G02 X{round(start_x - radius, 3)} Y{round(start_y, 3)} I{round(radius, 3)} J0"
        ]

    def arc_mill_submenu(self):
        self.clear_window()
        label = tk.Label(self.root, text="Frezowanie po łuku", font=("Arial", 16))
        label.pack(pady=10)
        def open_arc_clockwise():
            self.arc_mill_clockwise_submenu()
        def open_arc_counterclockwise():
            self.arc_mill_counterclockwise_submenu()
        def open_circle_mill():
            self.circle_mill_submenu()
        clockwise_btn = tk.Button(self.root, text="Łuk zgodnie z ruchem wskazówek", command=open_arc_clockwise)
        counterclockwise_btn = tk.Button(self.root, text="Łuk przeciwnie do wskazówek", command=open_arc_counterclockwise)
        circle_btn = tk.Button(self.root, text="Frezowanie okręgu", command=open_circle_mill)
        back_btn = tk.Button(self.root, text="Cofnij", command=self.add_data_to_program)
        clockwise_btn.pack(pady=5)
        counterclockwise_btn.pack(pady=5)
        circle_btn.pack(pady=5)
        back_btn.pack(pady=5)

    def arc_mill_clockwise_submenu(self):
        self.clear_window()
        self.create_arc_inputs("Frezowanie łuku zgodnie z ruchem wskazówek", "G2")

    def arc_mill_counterclockwise_submenu(self):
        self.clear_window()
        self.create_arc_inputs("Frezowanie łuku przeciwnie do ruchu wskazówek", "G3")

    def circle_mill_submenu(self):
        self.clear_window()
        label = tk.Label(self.root, text="Frezowanie okręgu", font=("Arial", 16))
        label.pack(pady=10)
        x_label = tk.Label(self.root, text="X (środek):")
        x_label.pack()
        x_entry = tk.Entry(self.root)
        x_entry.pack()
        y_label = tk.Label(self.root, text="Y (środek):")
        y_label.pack()
        y_entry = tk.Entry(self.root)
        y_entry.pack()
        radius_label = tk.Label(self.root, text="Promień:")
        radius_label.pack()
        radius_entry = tk.Entry(self.root)
        radius_entry.pack()
        def add_circle_mill_operation():
            try:
                x = float(x_entry.get().strip())
                y = float(y_entry.get().strip())
                radius = float(radius_entry.get().strip())
                if radius <= 0:
                    raise ValueError("Promień musi być większy od 0.")
                commands = self.circle_mill(x, y, radius)
                self.program_data.extend(commands)
                self.is_program_saved = False
                messagebox.showinfo("Dodano", f"Dodano operacje")
            except ValueError as e:
                messagebox.showerror("Błąd", f"Proszę wprowadzić poprawne wartości: {e}")
        add_btn = tk.Button(self.root, text="Dodaj operację", command=add_circle_mill_operation)
        add_btn.pack(pady=5)
        back_btn = tk.Button(self.root, text="Cofnij", command=self.arc_mill_submenu)
        back_btn.pack(pady=5)

    def create_arc_inputs(self, title, arc_function):
        label = tk.Label(self.root, text=title, font=("Arial", 16))
        label.pack(pady=10)
        x_label = tk.Label(self.root, text="X (pozycja końcowa):")
        x_label.pack()
        x_entry = tk.Entry(self.root)
        x_entry.pack()
        y_label = tk.Label(self.root, text="Y (pozycja końcowa):")
        y_label.pack()
        y_entry = tk.Entry(self.root)
        y_entry.pack()
        xk_label = tk.Label(self.root, text="I (przesunięcie względem X):")
        xk_label.pack()
        xk_entry = tk.Entry(self.root)
        xk_entry.pack()
        yk_label = tk.Label(self.root, text="J (przesunięcie względem Y):")
        yk_label.pack()
        yk_entry = tk.Entry(self.root)
        yk_entry.pack()
        radius_label = tk.Label(self.root, text="Promień (radius):")
        radius_label.pack()
        radius_entry = tk.Entry(self.root)
        radius_entry.pack()
        def add_arc_operation():
            try:
                x = float(x_entry.get().strip())
                y = float(y_entry.get().strip())
                xk = float(xk_entry.get().strip())
                yk = float(yk_entry.get().strip())
                if radius_entry.get().strip() != "":
                    radius = float(radius_entry.get().strip())
                    if radius <= 0:
                        raise ValueError("Promień musi być większy od 0.")
                else:
                    radius = 0
                if arc_function == "G2":
                    commands = self.arc_mill_clockwise(x, y, xk, yk, radius)
                else:
                    commands = self.arc_mill_counterclockwise(x, y, xk, yk, radius)
                self.program_data.extend(commands)
                self.is_program_saved = False
                messagebox.showinfo("Dodano", "Dodano operacje")
            except ValueError as e:
                messagebox.showerror("Błąd", f"Proszę wprowadzić poprawne wartości: {e}")
        add_btn = tk.Button(self.root, text="Dodaj operację", command=add_arc_operation)
        add_btn.pack(pady=5)
        back_btn = tk.Button(self.root, text="Cofnij", command=self.arc_mill_submenu)
        back_btn.pack(pady=5)

    def circular_pocket_mill(self, x, y, diameter, depth, stepdown, feedrate, tool_radius):
        commands = []
        initial_x = x
        commands.append(f"G0 X{round(x, 3)} Y{round(y, 3)} Z5")
        if feedrate != '' or feedrate != 0:
            commands.append(f"F{round(feedrate, 3)}")
        commands.append("M3")
        steps_number = depth / stepdown
        steps_down = []
        if steps_number % 1 != 0:
            step_down = 0
            last_step = depth - int(steps_number) * stepdown
            for i in range(int(steps_number)):
                step_down -= stepdown
                steps_down.append(step_down)
            steps_down.append(round(step_down - last_step, 3))
        else:
            step_down = 0
            for i in range(int(steps_number)):
                step_down -= stepdown
                steps_down.append(step_down)
        rotations_number = diameter / (tool_radius * 2)
        rotations_x = []
        if rotations_number % 1 != 0:
            rotations_number = int(rotations_number)
            last_rotation = x - diameter / 2 + tool_radius
            for i in range(rotations_number):
                rotations_x.append(x)
                x -= tool_radius
            if last_rotation != 0 and initial_x != 0:
                rotations_x.append(last_rotation)
                del rotations_x[0]
        else:
            for i in range(int(rotations_number)):
                x -= tool_radius
                rotations_x.append(x)
        current_radius = tool_radius
        for step_down in steps_down:
            current_radius = tool_radius
            commands.append(f"G01 X{initial_x} Y{y}")
            commands.append(f"G01 Z{step_down}")
            if initial_x != 24:
                for rotation in rotations_x:
                    if rotation == initial_x:
                        continue
                    commands.append(f"G01 X{rotation}")
                    if rotation != rotations_x[-1]:
                        commands.append(f"G02 X{rotation} Y{y} I{current_radius} J0 F{feedrate}")
                        current_radius += tool_radius
                    else:
                        current_radius = initial_x - rotations_x[-1]
                        commands.append(f"G02 X{rotation} Y{y} I{current_radius} J0 F{feedrate}")
        commands.append("G0 Z5")
        commands.append("M5")
        return commands

    def circular_pocket_submenu(self):
        self.clear_window()
        label = tk.Label(self.root, text="Frezowanie kieszeni okrągłej", font=("Arial", 16))
        label.pack(pady=10)
        inputs = {
            "X (środek)": tk.Entry(self.root),
            "Y (środek)": tk.Entry(self.root),
            "Średnica": tk.Entry(self.root),
            "Głębokość": tk.Entry(self.root),
            "Krok": tk.Entry(self.root),
            "Posuw (mm/min)": tk.Entry(self.root),
            "Promień narzędzia": tk.Entry(self.root)
        }
        for label_text, entry in inputs.items():
            tk.Label(self.root, text=label_text).pack()
            entry.pack()
        def add_circular_pocket_operation():
            try:
                x = float(inputs["X (środek)"].get().strip())
                y = float(inputs["Y (środek)"].get().strip())
                diameter = float(inputs["Średnica"].get().strip())
                depth = float(inputs["Głębokość"].get().strip())
                stepdown = float(inputs["Krok"].get().strip())
                feedrate_input = inputs["Posuw (mm/min)"].get().strip()
                tool_radius = float(inputs["Promień narzędzia"].get().strip())
                feedrate = float(feedrate_input) if feedrate_input else 0
                if diameter <= 0:
                    raise ValueError("Średnica musi być większa od 0.")
                if depth <= 0:
                    raise ValueError("Głębokość musi być większa od 0.")
                if stepdown <= 0:
                    raise ValueError("Krok musi być większy od 0.")
                if tool_radius <= 0:
                    raise ValueError("Promień narzędzia musi być większy od 0.")
                if stepdown > depth:
                    raise ValueError("Krok nie może być większy niż głębokość.")
                commands = self.circular_pocket_mill(x, y, diameter, depth, stepdown, feedrate, tool_radius)
                self.program_data.extend(commands)
                self.is_program_saved = False
                messagebox.showinfo("Sukces", "Operacja frezowania kieszeni okrągłej została dodana.")
            except ValueError as e:
                messagebox.showerror("Błąd", f"Proszę wprowadzić poprawne wartości: {e}")
        def confirm_back():
            if messagebox.askyesno("Powrót", "Czy na pewno chcesz wrócić?"):
                self.add_data_to_program()
        add_btn = tk.Button(self.root, text="Dodaj operację", command=add_circular_pocket_operation)
        add_btn.pack(pady=5)
        back_btn = tk.Button(self.root, text="Powrót", command=confirm_back)
        back_btn.pack(pady=5)

    def rectangular_pocket_mill(self, x, y, width, height, depth, stepdown, feedrate, tool_radius):
        commands = []
        num_passes = int(depth / stepdown) + 1
        commands.append(f"G0 X{round(x + tool_radius, 3)} Y{round(y + tool_radius, 3)} Z5")
        if feedrate > 0:
            commands.append(f"F{round(feedrate, 3)}")
        commands.append("M3")
        for pass_num in range(num_passes):
            z_depth = round(pass_num * stepdown, 3)
            if z_depth == 0.0:
                continue
            commands.append(f"G1 Z{-z_depth}")
            current_x = round(x + tool_radius, 3)
            current_y = round(y + tool_radius, 3)
            current_width = round(width - 2 * tool_radius, 3)
            current_height = round(height - 2 * tool_radius, 3)
            while current_width > 0 and current_height > 0:
                commands.append(f"G1 X{round(current_x, 3)} Y{round(current_y, 3)}")
                commands.append(f"G1 X{round(current_x + current_width, 3)} Y{round(current_y, 3)}")
                commands.append(f"G1 X{round(current_x + current_width, 3)} Y{round(current_y + current_height, 3)}")
                commands.append(f"G1 X{round(current_x, 3)} Y{round(current_y + current_height, 3)}")
                commands.append(f"G1 X{round(current_x, 3)} Y{round(current_y, 3)}")
                current_x = round(current_x + tool_radius, 3)
                current_y = round(current_y + tool_radius, 3)
                current_width = round(current_width - 2 * tool_radius, 3)
                current_height = round(current_height - 2 * tool_radius, 3)
        if width > height:
            fake_square_side = height / 2
            commands.append(f"G01 X{x + fake_square_side} Y{y + height - fake_square_side}")
        else:
            fake_square_side = width / 2
            commands.append(f"G01 X{x + fake_square_side} Y{y + fake_square_side}")
            commands.append(f"G01 X{x + width - tool_radius} Y{y + tool_radius}")
            commands.append(f"G01 X{x + fake_square_side} Y{y + fake_square_side}")
            commands.append(f"G01 X{x + fake_square_side} Y{y + height - fake_square_side}")
            commands.append(f"G01 X{x + tool_radius} Y{y + height - tool_radius}")
            commands.append(f"G01 X{x + fake_square_side} Y{y + height - fake_square_side}")
            commands.append(f"G01 X{x + width - tool_radius} Y{y + height - tool_radius}")
        commands.append("M5")
        return commands

    def face_mill_submenu(self):
        self.clear_window()
        label = tk.Label(self.root, text="Frezowanie czoła", font=("Arial", 16))
        label.pack(pady=10)
        inputs = {
            "X (lewy, dolny róg kieszeni)": tk.Entry(self.root),
            "Y (lewy, dolny róg kieszeni)": tk.Entry(self.root),
            "Szerokość kieszeni": tk.Entry(self.root),
            "Długość kieszeni": tk.Entry(self.root),
            "Głębokość kieszeni": tk.Entry(self.root),
            "Krok": tk.Entry(self.root),
            "Posuw (mm/min)": tk.Entry(self.root),
            "Promień narzędzia": tk.Entry(self.root)
        }
        for label_text, entry in inputs.items():
            tk.Label(self.root, text=label_text).pack()
            entry.pack()
        def add_face_mill_operation():
            try:
                x = float(inputs["X (lewy, dolny róg kieszeni)"].get().strip())
                y = float(inputs["Y (lewy, dolny róg kieszeni)"].get().strip())
                width = float(inputs["Szerokość kieszeni"].get().strip())
                height = float(inputs["Długość kieszeni"].get().strip())
                depth = float(inputs["Głębokość kieszeni"].get().strip())
                stepdown = float(inputs["Krok"].get().strip())
                feedrate = float(inputs["Posuw (mm/min)"].get().strip())
                tool_radius = float(inputs["Promień narzędzia"].get().strip())
                if width <= 0:
                    raise ValueError("Szerokość kieszeni musi być większa od 0.")
                if height <= 0:
                    raise ValueError("Długość kieszeni musi być większa od 0.")
                if depth <= 0:
                    raise ValueError("Głębokość kieszeni musi być większa od 0.")
                if stepdown <= 0:
                    raise ValueError("Krok musi być większy od 0.")
                if feedrate <= 0:
                    raise ValueError("Posuw (mm/min) musi być większy od 0.")
                if tool_radius <= 0:
                    raise ValueError("Promień narzędzia musi być większy od 0.")
                if stepdown > depth:
                    raise ValueError("Krok nie może być większy niż głębokość kieszeni.")
                commands = self.rectangular_pocket_mill(x, y, width, height, depth, stepdown, feedrate, tool_radius)
                self.program_data.extend(commands)
                self.is_program_saved = False
                messagebox.showinfo("Sukces", "Operacja frezowania czoła została dodana.")
            except ValueError as e:
                messagebox.showerror("Błąd", f"Proszę wprowadzić poprawne wartości: {e}")
        def confirm_back():
            if messagebox.askyesno("Powrót", "Czy na pewno chcesz wrócić?"):
                self.add_data_to_program()
        add_btn = tk.Button(self.root, text="Dodaj operację", command=add_face_mill_operation)
        add_btn.pack(pady=5)
        back_btn = tk.Button(self.root, text="Powrót", command=confirm_back)
        back_btn.pack(pady=5)

    def bore_material(self, x=None, y=None, z=None, feedrate=None):
        if z is None:
            raise ValueError("Z (głębokość) jest wymagana.")
        commands = []
        if x is not None:
            x = round(x, 3)
        if y is not None:
            y = round(y, 3)
        z = round(z, 3)
        if feedrate is not None:
            feedrate = round(feedrate, 3)
        position_command = "G00"
        if x is not None:
            position_command += f" X{x}"
        if y is not None:
            position_command += f" Y{y}"
        position_command += " Z5"
        commands.append(position_command)
        if feedrate is not None:
            commands.append(f"F{feedrate}")
        commands.append(f"G01 Z{-z}")
        commands.append("G00 Z5")
        return commands

    def bore_material_submenu(self):
        self.clear_window()
        label = tk.Label(self.root, text="Wwiercenie do materiału", font=("Arial", 16))
        label.pack(pady=10)
        x_label = tk.Label(self.root, text="X (opcjonalnie):")
        x_label.pack()
        x_entry = tk.Entry(self.root)
        x_entry.pack()
        y_label = tk.Label(self.root, text="Y (opcjonalnie):")
        y_label.pack()
        y_entry = tk.Entry(self.root)
        y_entry.pack()
        z_label = tk.Label(self.root, text="Głębokość (wymagane):")
        z_label.pack()
        z_entry = tk.Entry(self.root)
        z_entry.pack()
        feedrate_label = tk.Label(self.root, text="Posuw (mm/min) (opcjonalnie):")
        feedrate_label.pack()
        feedrate_entry = tk.Entry(self.root)
        feedrate_entry.pack()
        def add_bore_operation():
            try:
                z_value = z_entry.get().strip()
                if not z_value:
                    raise ValueError("Z (głębokość) jest wymagane.")
                z_value = float(z_value)
                x_value = x_entry.get().strip()
                x_value = float(x_value) if x_value else None
                y_value = y_entry.get().strip()
                y_value = float(y_value) if y_value else None
                feedrate_value = feedrate_entry.get().strip()
                feedrate_value = float(feedrate_value) if feedrate_value else None
                commands = self.bore_material(x=x_value, y=y_value, z=z_value, feedrate=feedrate_value)
                self.program_data.extend(commands)
                self.is_program_saved = False
                messagebox.showinfo("Dodano", "Dodano operacje")
            except ValueError as e:
                messagebox.showerror("Błąd", str(e))
        def confirm_back():
            if messagebox.askyesno("Powrót", "Czy na pewno chcesz wrócić?"):
                self.add_data_to_program()
        add_btn = tk.Button(self.root, text="Dodaj operację", command=add_bore_operation)
        add_btn.pack(pady=5)
        back_btn = tk.Button(self.root, text="Powrót", command=confirm_back)
        back_btn.pack(pady=5)

    def drill_material(self, x=None, y=None, z=None, feedrate=None):
        if z is None:
            raise ValueError("Z (depth) is required.")
        commands = []
        if x is not None:
            x = round(x, 3)
        if y is not None:
            y = round(y, 3)
        z = round(z, 3)
        if feedrate is not None:
            feedrate = round(feedrate, 3)
        position_command = "G00"
        if x is not None:
            position_command += f" X{x}"
        if y is not None:
            position_command += f" Y{y}"
        position_command += " Z5"
        commands.append(position_command)
        if feedrate is not None:
            commands.append(f"F{feedrate}")
        commands.append("M03")
        commands.append("M08")
        commands.append(f"G01 Z{-z}")
        commands.append("G00 Z5")
        commands.append("M09")
        return commands

    def drill_material_submenu(self):
        self.clear_window()
        label = tk.Label(self.root, text="Otwór", font=("Arial", 16))
        label.pack(pady=10)
        x_label = tk.Label(self.root, text="X (opcjonalnie):")
        x_label.pack()
        x_entry = tk.Entry(self.root)
        x_entry.pack()
        y_label = tk.Label(self.root, text="Y (opcjonalnie):")
        y_label.pack()
        y_entry = tk.Entry(self.root)
        y_entry.pack()
        z_label = tk.Label(self.root, text="Głębokość (wymagane):")
        z_label.pack()
        z_entry = tk.Entry(self.root)
        z_entry.pack()
        feedrate_label = tk.Label(self.root, text="Posuw (opcjonalnie):")
        feedrate_label.pack()
        feedrate_entry = tk.Entry(self.root)
        feedrate_entry.pack()
        def add_drill_operation():
            try:
                z_value = z_entry.get().strip()
                if not z_value:
                    raise ValueError("Z (głębokość) jest wymagane.")
                z_value = float(z_value)
                x_value = x_entry.get().strip()
                x_value = float(x_value) if x_value else None
                y_value = y_entry.get().strip()
                y_value = float(y_value) if y_value else None
                feedrate_value = feedrate_entry.get().strip()
                feedrate_value = float(feedrate_value) if feedrate_value else None
                commands = self.drill_material(x=x_value, y=y_value, z=z_value, feedrate=feedrate_value)
                self.program_data.extend(commands)
                self.is_program_saved = False
                messagebox.showinfo("Dodano", "Dodano operację")
            except ValueError as e:
                messagebox.showerror("Błąd", str(e))
        def confirm_back():
            if messagebox.askyesno("Powrót", "Czy na pewno chcesz wrócić?"):
                self.add_data_to_program()
        add_btn = tk.Button(self.root, text="Dodaj operację", command=add_drill_operation)
        add_btn.pack(pady=5)
        back_btn = tk.Button(self.root, text="Powrót", command=confirm_back)
        back_btn.pack(pady=5)

    def go_to_submenu(self):
        self.clear_window()
        label = tk.Label(self.root, text="Idź do X/Y/Z", font=("Arial", 16))
        label.pack(pady=10)
        x_label = tk.Label(self.root, text="X:")
        x_label.pack()
        x_entry = tk.Entry(self.root)
        x_entry.pack()
        y_label = tk.Label(self.root, text="Y:")
        y_label.pack()
        y_entry = tk.Entry(self.root)
        y_entry.pack()
        z_label = tk.Label(self.root, text="Z:")
        z_label.pack()
        z_entry = tk.Entry(self.root)
        z_entry.pack()
        def add_goto_operation():
            try:
                x_value = x_entry.get().strip()
                y_value = y_entry.get().strip()
                z_value = z_entry.get().strip()
                if not x_value and not y_value and not z_value:
                    raise ValueError("Podaj conajmniej jedną z wartości")
                x_value = float(x_value) if x_value else ""
                y_value = float(y_value) if y_value else ""
                z_value = float(z_value) if z_value else ""
                operation = self.go_to(x_value, y_value, z_value)
                self.program_data.append(operation)
                self.is_program_saved = False
                messagebox.showinfo("Dodano", "Dodano operację")
            except ValueError as e:
                messagebox.showerror("Błąd", str(e))
        def confirm_back():
            if messagebox.askyesno("Powrót", "Czy na pewno chcesz wrócić?"):
                self.add_data_to_program()
        add_btn = tk.Button(self.root, text="Dodaj operację", command=add_goto_operation)
        add_btn.pack(pady=5)
        back_btn = tk.Button(self.root, text="Powrót", command=confirm_back)
        back_btn.pack(pady=5)

    def go_to(self, x, y, z):
        ret_val = "G00"
        if x != "":
            ret_val += f" X{x}"
        if y != "":
            ret_val += f" Y{y}"
        if z != "":
            ret_val += f" Z{z}"
        return ret_val

    def mill_to_submenu(self):
        self.clear_window()
        label = tk.Label(self.root, text="Frezuj do X/Y/Z", font=("Arial", 16))
        label.pack(pady=10)
        x_label = tk.Label(self.root, text="X:")
        x_label.pack()
        x_entry = tk.Entry(self.root)
        x_entry.pack()
        y_label = tk.Label(self.root, text="Y:")
        y_label.pack()
        y_entry = tk.Entry(self.root)
        y_entry.pack()
        z_label = tk.Label(self.root, text="Z:")
        z_label.pack()
        z_entry = tk.Entry(self.root)
        z_entry.pack()
        f_label = tk.Label(self.root, text="Posuw (mm/min):")
        f_label.pack()
        f_entry = tk.Entry(self.root)
        f_entry.pack()
        def add_millto_operation():
            try:
                x_value = x_entry.get().strip()
                y_value = y_entry.get().strip()
                z_value = z_entry.get().strip()
                f_value = f_entry.get().strip()
                if not x_value and not y_value and not z_value:
                    raise ValueError("Podaj conajmniej jedną z wartości (X, Y, Z)")
                x_value = float(x_value) if x_value else ""
                y_value = float(y_value) if y_value else ""
                z_value = float(z_value) if z_value else ""
                f_value = float(f_value) if f_value else ""
                operation = self.mill_to(x_value, y_value, z_value, f_value)
                self.program_data.append(operation)
                self.is_program_saved = False
                messagebox.showinfo("Dodano", "Dodano operację")
            except ValueError as e:
                messagebox.showerror("Błąd", str(e))
        def confirm_back():
            if messagebox.askyesno("Powrót", "Czy na pewno chcesz wrócić?"):
                self.add_data_to_program()
        add_btn = tk.Button(self.root, text="Dodaj operację", command=add_millto_operation)
        add_btn.pack(pady=5)
        back_btn = tk.Button(self.root, text="Powrót", command=confirm_back)
        back_btn.pack(pady=5)

    def mill_to(self, x, y, z, f):
        ret_val = "G01"
        if x != "":
            ret_val += f" X{x}"
        if y != "":
            ret_val += f" Y{y}"
        if z != "":
            ret_val += f" Z{z}"
        if f != "":
            ret_val += f" F{f}"
        return ret_val

    def change_feed_prompt(self):
        while True:
            try:
                feed_value = simpledialog.askfloat("Zmiana Posuw (mm/min)u", "Podaj wartość Posuw (mm/min)u:")
                if feed_value and feed_value > 0:
                    self.program_data.append(f"F{feed_value}")
                    self.is_program_saved = False
                    messagebox.showinfo("Dodano", f"Dodano Posuw (mm/min): F{feed_value}")
                    break
                elif feed_value is None:
                    break
                else:
                    messagebox.showerror("Błąd", "Wartość Posuw (mm/min)u musi być większa od 0.")
            except ValueError:
                messagebox.showerror("Błąd", "Proszę wprowadzić poprawną wartość liczbową.")

    def units_submenu(self):
        self.clear_window()
        label = tk.Label(self.root, text="Zmień jednostki", font=("Arial", 16))
        label.pack(pady=10)
        metric_btn = tk.Button(self.root, text="Ustaw jednostki na metryczne", command=self.set_metric_units)
        imperial_btn = tk.Button(self.root, text="Ustaw jednostki na imperialne", command=self.set_imperial_units)
        metric_btn.pack(pady=5)
        imperial_btn.pack(pady=5)
        back_btn = tk.Button(self.root, text="Powrót do poprzedniego menu", command=lambda: self.submenu("Dodaj dane do programu"))
        back_btn.pack(pady=5)

    def set_metric_units(self):
        self.program_data.append("G21")
        self.is_program_saved = False

    def set_imperial_units(self):
        self.program_data.append("G20")
        self.is_program_saved = False

    def change_tool_prompt(self):
        tool_number = simpledialog.askinteger("Zmień narzędzie", "Podaj numer narzędzia (1-6)")
        tool_radius = simpledialog.askfloat("Średnica narzędzia", "Podaj średnicę narzędzia")
        if tool_number and 1 <= tool_number <= 6 and tool_radius > 0 and tool_radius < self.max_tool_radius:
            tool_setting = self.change_tool(tool_number, tool_radius)
            self.program_data.append(tool_setting)
            self.is_program_saved = False
            messagebox.showinfo("Narzedzie zmienione", f"Zmieniono narzędzie na {tool_setting}")
        if 1 > tool_number > 6:
            messagebox.showerror("Błąd", "Numer narzędzia musi być w zakresie od 1 do 6.")
        if tool_radius <= 0.0:
            messagebox.showerror("Błąd", f"Średnica musi być w zakresie od 0 do {self.max_tool_radius * 2}")

    def change_tool(self, tool_number, tool_radius):
        return f"T{tool_number} M6 ; SREDNICA {tool_radius * 2}"

    def add_operation(self, operation_name):
        self.program_data.append(operation_name)
        self.is_program_saved = False

    def confirm_exit_to_main_menu(self):
        if not self.is_program_saved:
            if messagebox.askyesno("Zapisz zmiany", "Czy zapisać program przed wyjściem?"):
                self.save_file()
        self.main_menu()

    def save_program(self):
        if not self.nazwa_programu:
            messagebox.showerror("Błąd", "Nie można zapisać programu bez nazwy.")
            return
        filename = f"{self.nazwa_programu}.gcode"
        try:
            self.save_to_file(self.program_data, filename)
            self.is_program_saved = True
            messagebox.showinfo("Zapisano", f"Program '{self.nazwa_programu}' został zapisany w pliku '{filename}'.")
        except Exception as e:
            messagebox.showerror("Błąd zapisu", f"Nie udało się zapisać programu: {e}")

    def save_to_file(self, array, filename):
        with open(filename, 'w') as file:
            if isinstance(array, list):
                for item in array:
                    file.write(f"{item}\n")
            else:
                file.write(array)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def coolant_control_submenu(self):
        self.clear_window()
        label = tk.Label(self.root, text="Włącz/Wyłącz chłodziwo", font=("Arial", 16))
        label.pack(pady=10)
        coolant_on_btn = tk.Button(self.root, text="Włącz chłodziwo", command=self.coolant_on)
        coolant_off_btn = tk.Button(self.root, text="Wyłącz chłodziwo", command=self.coolant_off)
        back_btn = tk.Button(self.root, text="Powrót", command=lambda: self.submenu("Dodaj dane do programu"))
        coolant_on_btn.pack(pady=5)
        coolant_off_btn.pack(pady=5)
        back_btn.pack(pady=5)

    def coolant_on(self):
        self.program_data.append("M08")
        self.is_program_saved = False

    def coolant_off(self):
        self.program_data.append("M09")
        self.is_program_saved = False
        
    def _update_window_min_size(self):
        self.root.update_idletasks()
        if self.root.winfo_children():
            main_frame = self.root.winfo_children()[0]
            required_height = main_frame.winfo_reqheight() + 20
            self.root.minsize(self.default_width, required_height)
        else:
            self.root.minsize(self.default_width, 0)

    def calculate_machining_time(self):
        total_time_seconds = 0.0
        current_position = [0.0, 0.0, 5.0]
        current_feedrate = 1000

        for cmd in self.program_data:
            parsed = GCodeParser.parse(
                cmd, 
                current_position,
                current_feedrate
            )
            
            if parsed.get('type') == 'UPDATE_FEED':
                current_feedrate = parsed['f']
                continue
            elif 'f' in parsed:
                current_feedrate = parsed['f']
            
            if parsed['type'] in ['G01', 'ARC']:
                distance = self._calculate_move_distance(parsed, current_position)
                if current_feedrate > 0:
                    total_time_seconds += (distance / current_feedrate) * 60
            
            self._update_position(current_position, parsed)

        return self._format_time(total_time_seconds)

    def _calculate_move_distance(self, parsed, current_pos):
        if parsed['type'] == 'ARC':
            radius = parsed['radius']
            angle = abs(parsed['end_angle'] - parsed['start_angle'])
            arc_length_xy = radius * angle
            dz = parsed['z'] - current_pos[2]
            return math.sqrt(arc_length_xy**2 + dz**2)
        else:
            dx = parsed.get('x', current_pos[0]) - current_pos[0]
            dy = parsed.get('y', current_pos[1]) - current_pos[1]
            dz = parsed.get('z', current_pos[2]) - current_pos[2]
            return math.sqrt(dx**2 + dy**2 + dz**2)

    def _update_current_position(self, parsed, current_pos):
        if parsed['type'] in ['G00', 'G01']:
            current_pos[0] = parsed.get('x', current_pos[0])
            current_pos[1] = parsed.get('y', current_pos[1])
            current_pos[2] = parsed.get('z', current_pos[2])
        elif parsed['type'] == 'ARC':
            current_pos[0] = parsed['x']
            current_pos[1] = parsed['y']
            current_pos[2] = parsed['z']

    def _update_position(self, current_pos, parsed):
        if parsed['type'] in ['G00', 'G01', 'ARC']:
            current_pos[0] = parsed.get('x', current_pos[0])
            current_pos[1] = parsed.get('y', current_pos[1])
            current_pos[2] = parsed.get('z', current_pos[2])

    def _format_time(self, total_seconds):
        total_seconds = int(round(total_seconds))
        hours = total_seconds // 3600
        remainder = total_seconds % 3600
        minutes = remainder // 60
        seconds = remainder % 60
        
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def show_machining_time(self):
        try:
            formatted_time = self.calculate_machining_time()
            messagebox.showinfo(
                "Czas obróbki", 
                f"Szacowany czas: {formatted_time}\n"
            )
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd obliczeń: {str(e)}")

            

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()