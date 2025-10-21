"""
Helper para anotação de ground truth OCR
Interface simples para anotar texto das imagens
"""
import argparse
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import cv2
from PIL import Image, ImageTk


class GroundTruthAnnotator:
    def __init__(self, images_dir: Path, gt_path: Path):
        self.images_dir = images_dir
        self.gt_path = gt_path
        
        # Carregar ou criar ground truth
        if gt_path.exists():
            with open(gt_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.annotations = data.get('annotations', {})
        else:
            self.annotations = {}
        
        # Lista de imagens
        self.image_files = sorted(images_dir.glob("*.jpg"))
        self.current_index = 0
        
        # Encontrar primeira imagem não anotada
        for idx, img_file in enumerate(self.image_files):
            if img_file.name not in self.annotations or not self.annotations[img_file.name]:
                self.current_index = idx
                break
        
        # Setup GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Configura interface gráfica"""
        self.root = tk.Tk()
        self.root.title("Ground Truth Annotator - OCR")
        self.root.geometry("800x600")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Informações
        info_text = f"Total: {len(self.image_files)} imagens | " \
                   f"Anotadas: {sum(1 for v in self.annotations.values() if v)}"
        self.info_label = ttk.Label(main_frame, text=info_text)
        self.info_label.grid(row=0, column=0, columnspan=3, pady=5)
        
        # Canvas para imagem
        self.canvas = tk.Canvas(main_frame, width=600, height=400, bg='gray')
        self.canvas.grid(row=1, column=0, columnspan=3, pady=10)
        
        # Label do arquivo
        self.file_label = ttk.Label(main_frame, text="", font=('Arial', 10, 'bold'))
        self.file_label.grid(row=2, column=0, columnspan=3, pady=5)
        
        # Entry para texto
        ttk.Label(main_frame, text="Texto da data de validade:").grid(row=3, column=0, columnspan=3, pady=5)
        self.text_entry = ttk.Entry(main_frame, width=50, font=('Arial', 12))
        self.text_entry.grid(row=4, column=0, columnspan=3, pady=5)
        self.text_entry.bind('<Return>', lambda e: self.save_and_next())
        
        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="← Anterior", command=self.previous_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Salvar e Próxima →", command=self.save_and_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Pular", command=self.next_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Salvar Tudo", command=self.save_all).pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=len(self.image_files))
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Carregar primeira imagem
        self.load_image()
        
        # Focus no entry
        self.text_entry.focus()
        
    def load_image(self):
        """Carrega e exibe imagem atual"""
        if not self.image_files:
            return
        
        img_path = self.image_files[self.current_index]
        
        # Carregar imagem
        image = cv2.imread(str(img_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Redimensionar para caber no canvas
        h, w = image.shape[:2]
        max_w, max_h = 600, 400
        
        scale = min(max_w / w, max_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        image = cv2.resize(image, (new_w, new_h))
        
        # Converter para PhotoImage
        pil_image = Image.fromarray(image)
        self.photo = ImageTk.PhotoImage(pil_image)
        
        # Exibir no canvas
        self.canvas.delete("all")
        x = (600 - new_w) // 2
        y = (400 - new_h) // 2
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
        
        # Atualizar labels
        self.file_label.config(text=f"Arquivo: {img_path.name} ({self.current_index + 1}/{len(self.image_files)})")
        
        # Carregar texto existente
        existing_text = self.annotations.get(img_path.name, "")
        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, existing_text)
        
        # Atualizar progress bar
        self.progress_var.set(self.current_index + 1)
        
        # Atualizar info
        annotated_count = sum(1 for v in self.annotations.values() if v)
        info_text = f"Total: {len(self.image_files)} imagens | " \
                   f"Anotadas: {annotated_count} | " \
                   f"Restantes: {len(self.image_files) - annotated_count}"
        self.info_label.config(text=info_text)
        
    def save_current(self):
        """Salva anotação atual"""
        if not self.image_files:
            return
        
        img_path = self.image_files[self.current_index]
        text = self.text_entry.get().strip()
        self.annotations[img_path.name] = text
        
    def save_all(self):
        """Salva todas as anotações em arquivo"""
        self.save_current()
        
        data = {
            "annotations": self.annotations,
            "instructions": "Texto correto da data de validade em cada imagem"
        }
        
        with open(self.gt_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        annotated_count = sum(1 for v in self.annotations.values() if v)
        print(f"✅ {annotated_count} anotações salvas em {self.gt_path}")
        
    def next_image(self):
        """Próxima imagem"""
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.load_image()
            self.text_entry.focus()
        
    def previous_image(self):
        """Imagem anterior"""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()
            self.text_entry.focus()
        
    def save_and_next(self):
        """Salva e vai para próxima"""
        self.save_current()
        self.next_image()
        
    def run(self):
        """Executa aplicação"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """Ao fechar janela"""
        self.save_all()
        self.root.destroy()


def parse_args():
    parser = argparse.ArgumentParser(description="Anotar ground truth OCR")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/ocr_test",
        help="Diretório com imagens OCR"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("="*60)
    print("📝 GROUND TRUTH ANNOTATOR - OCR")
    print("="*60)
    print()
    
    data_dir = Path(args.data_dir)
    images_dir = data_dir / "images"
    gt_path = data_dir / "ground_truth.json"
    
    if not images_dir.exists():
        print(f"❌ Pasta de imagens não encontrada: {images_dir}")
        print("💡 Execute primeiro: make ocr-prepare-data")
        return
    
    image_count = len(list(images_dir.glob("*.jpg")))
    print(f"📂 Diretório: {data_dir}")
    print(f"📸 Imagens encontradas: {image_count}")
    print()
    print("💡 INSTRUÇÕES:")
    print("  - Digite o texto da data de validade conforme aparece na imagem")
    print("  - Pressione ENTER ou 'Salvar e Próxima' para avançar")
    print("  - Use os botões '← Anterior' e 'Pular' para navegar")
    print("  - As anotações são salvas automaticamente ao fechar")
    print()
    print("🚀 Iniciando interface...")
    print()
    
    try:
        app = GroundTruthAnnotator(images_dir, gt_path)
        app.run()
    except ImportError:
        print("❌ Erro: tkinter não está disponível")
        print("💡 Anote manualmente o arquivo:", gt_path)
        print()
        print("Formato JSON:")
        print("""{
  "annotations": {
    "crop_0000.jpg": "31/12/2025",
    "crop_0001.jpg": "15/06/2024"
  }
}""")


if __name__ == "__main__":
    main()
