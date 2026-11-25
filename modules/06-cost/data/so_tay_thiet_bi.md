# Sổ tay thiết bị — Phòng thí nghiệm Vật liệu Acme (hư cấu)

Tài liệu này là dữ liệu mẫu tự viết cho module 06. Tên phòng, thiết bị và con số đều hư cấu.
Nó đủ dài để vượt ngưỡng token tối thiểu của prompt caching, nên dùng làm phần "đầu prompt" dùng lại.

## 1. Quy tắc chung

1. Đăng ký thiết bị trên bảng lịch ít nhất 24 giờ trước khi dùng.
2. Ghi sổ nhật ký mỗi lần dùng: ngày, giờ bắt đầu, giờ kết thúc, người dùng, mẫu đo, sự cố.
3. Không tự sửa thiết bị. Báo trưởng nhóm kỹ thuật khi có cảnh báo hoặc tiếng kêu lạ.
4. Tắt thiết bị theo đúng quy trình ở mục tương ứng trước khi rời phòng.
5. Mẫu đo phải có nhãn: mã mẫu, ngày chuẩn bị, người chuẩn bị.

## 2. Máy đo độ cứng vi mô HV-200

- Tải đo: từ 0,1 N tới 10 N. Thời gian giữ tải mặc định 15 giây.
- Hiệu chuẩn bằng khối chuẩn mỗi tuần một lần, sai số cho phép 2 %.
- Mẫu phải được mài và đánh bóng; bề mặt nghiêng quá 2 độ cho kết quả sai.
- Mỗi mẫu đo ít nhất 5 điểm, cách mép mẫu tối thiểu 2,5 lần đường chéo vết đâm.
- Ghi giá trị trung bình và độ lệch chuẩn. Loại điểm có vết đâm méo.

## 3. Lò nung ống LN-1200

- Nhiệt độ làm việc tối đa 1.150 °C; không vượt 1.200 °C dù chỉ vài phút.
- Tốc độ gia nhiệt khuyến nghị 5 °C mỗi phút; tốc độ làm nguội tự nhiên.
- Khí bảo vệ: argon, lưu lượng 0,5 lít mỗi phút, mở khí 15 phút trước khi gia nhiệt.
- Chương trình nung lưu tối đa 20 bước; kiểm tra lại từng bước trước khi chạy.
- Chỉ mở cửa lò khi nhiệt độ dưới 80 °C.

## 4. Máy quang phổ UV-Vis QS-3

- Bật đèn trước 30 phút để ổn định.
- Đo nền bằng cuvet chứa dung môi trước mỗi loạt mẫu.
- Dải bước sóng 190 tới 1.100 nm; độ phân giải 1 nm.
- Độ hấp thụ đáng tin trong khoảng 0,1 tới 1,5. Ngoài khoảng này thì pha loãng mẫu.
- Rửa cuvet bằng nước cất ba lần, lau bằng giấy không xơ.

## 5. Cân phân tích CP-220

- Khả năng cân tối đa 220 g, độ đọc 0,1 mg.
- Kiểm tra bọt thuỷ trước khi cân. Cân phải đặt trên bàn chống rung.
- Đóng cửa kính khi cân, chờ số ổn định ít nhất 5 giây.
- Hiệu chuẩn nội mỗi ngày bằng chức năng tự hiệu chuẩn.

## 6. Bảo trì định kỳ

| Thiết bị | Việc | Chu kỳ |
|---|---|---|
| HV-200 | Hiệu chuẩn bằng khối chuẩn | 7 ngày |
| LN-1200 | Kiểm tra cặp nhiệt và gioăng cửa | 30 ngày |
| QS-3 | Kiểm tra cường độ đèn | 90 ngày |
| CP-220 | Hiệu chuẩn ngoài bằng quả cân chuẩn | 180 ngày |

## 7. Xử lý sự cố thường gặp

- HV-200 báo "tải không ổn định": kiểm tra bàn đỡ mẫu đã khoá chưa, rồi đo lại.
- LN-1200 không đạt nhiệt độ đặt: kiểm tra cầu chì và cặp nhiệt; ghi sổ và báo kỹ thuật.
- QS-3 có đường nền trôi: để đèn ổn định thêm 15 phút, đo lại nền.
- CP-220 nhảy số: kiểm tra luồng gió, đóng cửa kính, kiểm tra bàn chống rung.

## 8. Liên hệ

Trưởng nhóm kỹ thuật: xem bảng tin của phòng. Ngoài giờ hành chính: ghi sự cố vào sổ và báo vào sáng hôm sau.
