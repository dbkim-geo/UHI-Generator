import tkinter as tk
from tkinter import filedialog, messagebox
import os
from osgeo import gdal, ogr
import pandas as pd
import matplotlib.pyplot as plt


class UHIAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UHI Analyzer (LST to CSV)")
        self.root.geometry("500x400")

        # LST 파일 선택
        tk.Label(root, text="LST 파일 선택:").pack()
        self.lst_file_label = tk.Label(root, text="선택된 파일: 없음", fg="blue")
        self.lst_file_label.pack()
        tk.Button(root, text="파일 선택", command=self.select_lst_file).pack()

        # 중심 좌표 입력 방식 선택
        tk.Label(root, text="중심 좌표 입력 방식:").pack()
        self.coord_method = tk.StringVar(value="manual")
        tk.Radiobutton(root, text="직접 입력", variable=self.coord_method, value="manual", command=self.toggle_coord_input).pack()
        tk.Radiobutton(root, text="Shapefile 사용", variable=self.coord_method, value="shapefile", command=self.toggle_coord_input).pack()

        # 프레임 생성 (좌표 입력 / Shapefile 선택)
        self.coord_frame = tk.Frame(root)
        self.coord_frame.pack()

        # 기본 좌표
        self.default_x = "320953"
        self.default_y = "4159672"

        # 직접 입력 필드
        self.x_label = tk.Label(self.coord_frame, text="X:")
        self.x_entry = tk.Entry(self.coord_frame, width=10)
        self.x_entry.insert(0, self.default_x)  # 기본값 설정

        self.y_label = tk.Label(self.coord_frame, text="Y:")
        self.y_entry = tk.Entry(self.coord_frame, width=10)
        self.y_entry.insert(0, self.default_y)  # 기본값 설정

        # Shapefile 선택 버튼
        self.shp_button = tk.Button(self.coord_frame, text="Shapefile 선택", command=self.select_shapefile, state="disabled")
        self.shp_file_label = tk.Label(self.coord_frame, text="선택된 파일: 없음", fg="blue")

        # 기본 상태: 직접 입력 필드 표시
        self.show_manual_input()

        # 출력 경로 선택
        tk.Label(root, text="출력 경로:").pack()
        self.output_dir_label = tk.Label(root, text="선택된 경로: ./", fg="blue")
        self.output_dir_label.pack()
        tk.Button(root, text="출력 경로 선택", command=self.select_output_dir).pack()

        # 파일 이름 입력
        tk.Label(root, text="파일 이름:").pack()
        self.filename_entry = tk.Entry(root)
        self.filename_entry.insert(0, "output.csv")
        self.filename_entry.pack()

        # 변환 버튼
        tk.Button(root, text="변환 시작", command=self.start_conversion).pack()

        # 진행 상태 표시
        self.status_label = tk.Label(root, text="진행 상태: 대기 중", fg="green")
        self.status_label.pack()

        # 변수 초기화
        self.lst_file = None
        self.output_dir = "./"

    def select_lst_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("GeoTIFF Files", "*.tif")])
        if file_path:
            self.lst_file = file_path
            self.lst_file_label.config(text=f"선택된 파일: {os.path.basename(file_path)}")

    def select_shapefile(self):
        file_path = filedialog.askopenfilename(filetypes=[("Shapefile", "*.shp")])
        if file_path:
            self.shp_file_label.config(text=f"선택된 파일: {os.path.basename(file_path)}")
            self.extract_coords_from_shapefile(file_path)

    def select_output_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_label.config(text=f"선택된 경로: {dir_path}")

    def toggle_coord_input(self):
        """ 중심 좌표 입력 방식 변경 시 UI 업데이트 """
        method = self.coord_method.get()
        if method == "manual":
            self.show_manual_input()
        else:
            self.show_shapefile_input()

    def show_manual_input(self):
        """ 직접 입력 필드를 표시하고 Shapefile 입력은 숨김 """
        self.clear_coord_frame()

        self.x_label.pack(side="left")
        self.x_entry.pack(side="left")
        self.y_label.pack(side="left")
        self.y_entry.pack(side="left")

        # 직접 입력 선택 시 기본 좌표 유지
        if not self.x_entry.get():
            self.x_entry.insert(0, self.default_x)
        if not self.y_entry.get():
            self.y_entry.insert(0, self.default_y)

    def show_shapefile_input(self):
        """ Shapefile 선택 버튼을 표시하고 직접 입력 필드는 숨김 """
        self.clear_coord_frame()
        self.shp_button.pack()
        self.shp_file_label.pack()

    def clear_coord_frame(self):
        """ 중심 좌표 입력 방식 전환 시 기존 UI 요소 제거 """
        for widget in self.coord_frame.winfo_children():
            widget.pack_forget()

    def extract_coords_from_shapefile(self, shp_path):
        """ GDAL/OGR을 사용하여 Shapefile에서 첫 번째 좌표 추출 """
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataset = driver.Open(shp_path, 0)
        if dataset is None:
            messagebox.showerror("오류", "Shapefile을 열 수 없습니다.")
            return

        layer = dataset.GetLayer()
        feature = layer.GetNextFeature()
        if feature:
            geom = feature.GetGeometryRef()
            x, y = geom.GetX(), geom.GetY()
            self.x_entry.delete(0, tk.END)
            self.x_entry.insert(0, str(x))
            self.y_entry.delete(0, tk.END)
            self.y_entry.insert(0, str(y))

    def start_conversion(self):
        if not self.lst_file:
            messagebox.showerror("오류", "LST(GeoTIFF) 파일을 선택하세요.")
            return

        x_coord = self.x_entry.get()
        y_coord = self.y_entry.get()
        if not x_coord or not y_coord:
            messagebox.showerror("오류", "중심 좌표를 입력하세요.")
            return

        output_filename = self.filename_entry.get()
        if not output_filename.endswith(".csv"):
            output_filename += ".csv"
        output_path = os.path.join(self.output_dir, output_filename)

        # LST 데이터 처리 시작
        self.status_label.config(text="진행 상태: 변환 중...", fg="orange")
        self.root.update()

        try:
            dataset = gdal.Open(self.lst_file)
            band = dataset.GetRasterBand(1)
            lst_array = band.ReadAsArray()

            # GeoTIFF의 좌표 변환 정보 가져오기
            transform = dataset.GetGeoTransform()
            pixel_width, pixel_height = transform[1], transform[5]  # 픽셀 크기
            origin_x, origin_y = transform[0], transform[3]  # 좌상단 좌표

            # 중심 좌표를 픽셀 좌표로 변환
            col = int((float(x_coord) - origin_x) / pixel_width)
            row = int((float(y_coord) - origin_y) / pixel_height)

            # 4가지 방향 정의 (동-서, 남-북, NW-SE, NE-SW)
            directions = {
                "West-East": [("West", 0, -1), ("East", 0, 1)],
                "North-South": [("North", -1, 0), ("South", 1, 0)],
                "Northwest-Southeast": [("Northwest", -1, -1), ("Southeast", 1, 1)],
                "Northeast-Southwest": [("Northeast", -1, 1), ("Southwest", 1, -1)]
            }

            # 데이터 저장용 리스트
            data = []

            # 각 방향으로 끝까지 이동하며 Grid 값 추출
            for direction, steps in directions.items():
                for sub_direction, row_step, col_step in steps:
                    distance = 0
                    new_row, new_col = row, col
                    
                    while 0 <= new_row < lst_array.shape[0] and 0 <= new_col < lst_array.shape[1]:
                        lst_value = lst_array[new_row, new_col]
                        data.append([direction, sub_direction, distance, lst_value])

                        # 다음 위치 이동
                        new_row += row_step
                        new_col += col_step
                        distance += 1

            # DataFrame 생성 후 저장
            df = pd.DataFrame(data, columns=["Direction", "Sub-Direction", "Distance", "LST Value"])
            df.to_csv(output_path, index=False)

            self.status_label.config(text=f"진행 상태: ✅ 변환 완료! ({output_filename})", fg="green")
            messagebox.showinfo("완료", f"CSV 저장 완료: {output_path}")

            # # 변환 후 그래프 창 실행
            # self.show_graph(output_path)

        except Exception as e:
            self.status_label.config(text="진행 상태: ❌ 오류 발생", fg="red")
            messagebox.showerror("오류", f"처리 중 오류 발생: {str(e)}")


    def show_graph(self, csv_path):
        """저장된 CSV 데이터를 불러와 그래프를 그리는 창을 생성"""
        try:
            df = pd.read_csv(csv_path)

            # 새로운 Tkinter 창 생성
            graph_window = tk.Toplevel(self.root)
            graph_window.title("LST 분석 그래프")
            graph_window.geometry("800x600")

            # Matplotlib Figure 생성
            fig, ax = plt.subplots(figsize=(8, 6))

            # 4가지 방향에 대한 LST 값 플로팅
            directions = df["Direction"].unique()
            for direction in directions:
                subset = df[df["Direction"] == direction]
                ax.plot(subset["Distance"], subset["LST Value"], marker="o", linestyle="-", label=direction)

            ax.set_title("LST 변화 분석")
            ax.set_xlabel("Distance from Center")
            ax.set_ylabel("LST Value")
            ax.legend()
            ax.grid(True)

            # Matplotlib을 Tkinter에서 렌더링
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            canvas = FigureCanvasTkAgg(fig, master=graph_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("오류", f"그래프를 생성하는 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = UHIAnalyzerApp(root)
    root.mainloop()
