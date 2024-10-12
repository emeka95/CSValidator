import tkinter as tk
from tkinter import ttk, filedialog as fd
# import os
import Main2 as Main


root = tk.Tk()
root.title('CSValidator')
root.geometry('500x200')


rules_label = tk.Label(master=root, text='Rules:')
rules_combobox = ttk.Combobox(master=root, width=40)
rules_label.grid(row=0, column=0, padx=10, sticky='w')
rules_combobox.grid(row=0, column=1, padx=10, sticky='w', pady=5)


def validate():
    rule_set = rules_combobox.get()
    if rule_set in ('', None):
        return  # TODO display an error
    target_file = fd.askopenfile(title='Select a CSV file to validate', filetypes=[('CSV file', '*.csv')])
    print(f'Validating file: {target_file}\nAgainst rule set: {rule_set}')


run_btn = ttk.Button(master=root, text='Validate', command=validate)
run_btn.grid(row=1, column=1, sticky='w', padx=10)


root.mainloop()