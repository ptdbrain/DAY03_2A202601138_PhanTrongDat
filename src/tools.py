"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.

Chủ đề nhóm: TƯ VẤN KHÓA HỌC ONLINE
- Kiến thức chung (lộ trình học, so sánh hình thức học) -> Chatbot tự trả lời, KHÔNG cần tool.
- Dữ liệu thực tế (danh sách khóa học, điểm đánh giá của học viên) -> BẮT BUỘC gọi tool.

Quy ước chung của tất cả tool trong file này (HỢP ĐỒNG AN TOÀN - Mốc 3):
- Tham số đầu vào: kiểu str.
- Giá trị trả về: LUÔN là str (để Agent đưa thẳng vào phần Observation).
- TUYỆT ĐỐI KHÔNG raise Exception ra ngoài. Mọi lỗi đều được nuốt và chuyển thành
  chuỗi thông báo, để vòng lặp ReAct trong app.py không bị crash giữa chừng:
    * "LỖI: ..."     -> sai tham số / không tìm thấy dữ liệu / lỗi hệ thống.
    * "TỪ CHỐI: ..." -> yêu cầu vi phạm chính sách an toàn.
  Agent đọc được chuỗi này và có thể tự sửa Action ở vòng lặp tiếp theo.
"""

# ---------------------------------------------------------------------------
# 📚 MOCK DATABASE - Dữ liệu khóa học mô phỏng (Coursera / Udemy / YouTube)
# ---------------------------------------------------------------------------
COURSE_DB = {
    "data analysis": [
        {
            "name": "Google Data Analytics Professional Certificate",
            "platform": "Coursera",
            "level": "Người mới bắt đầu",
            "duration": "6 tháng (10 giờ/tuần)",
            "price": "49 USD/tháng",
        },
        {
            "name": "Data Analysis with Python",
            "platform": "freeCodeCamp (YouTube)",
            "level": "Người mới bắt đầu",
            "duration": "10 giờ",
            "price": "Miễn phí",
        },
        {
            "name": "The Complete Data Analyst Bootcamp",
            "platform": "Udemy",
            "level": "Cơ bản đến Trung cấp",
            "duration": "35 giờ",
            "price": "399,000 VNĐ",
        },
    ],
    "machine learning": [
        {
            "name": "Machine Learning Specialization (Andrew Ng)",
            "platform": "Coursera",
            "level": "Cơ bản",
            "duration": "2 tháng (9 giờ/tuần)",
            "price": "49 USD/tháng",
        },
        {
            "name": "Machine Learning for Everybody",
            "platform": "freeCodeCamp (YouTube)",
            "level": "Người mới bắt đầu",
            "duration": "4 giờ",
            "price": "Miễn phí",
        },
        {
            "name": "Machine Learning A-Z: AI, Python & R",
            "platform": "Udemy",
            "level": "Cơ bản đến Trung cấp",
            "duration": "44 giờ",
            "price": "449,000 VNĐ",
        },
    ],
    "python": [
        {
            "name": "Python for Everybody Specialization",
            "platform": "Coursera",
            "level": "Người mới bắt đầu",
            "duration": "3 tháng (6 giờ/tuần)",
            "price": "49 USD/tháng",
        },
        {
            "name": "100 Days of Code: The Complete Python Pro Bootcamp",
            "platform": "Udemy",
            "level": "Người mới bắt đầu",
            "duration": "60 giờ",
            "price": "449,000 VNĐ",
        },
    ],
}

# ---------------------------------------------------------------------------
# ⭐ MOCK DATABASE - Đánh giá (review) của học viên đi trước
# ---------------------------------------------------------------------------
REVIEW_DB = {
    "machine learning for everybody": {
        "rating": 4.7,
        "total_reviews": 12500,
        "pros": "Giảng viên nói dễ hiểu, đi thẳng vào code, hoàn toàn miễn phí.",
        "cons": "Phần toán giải thích hơi nhanh, ít bài tập thực hành có chấm điểm.",
    },
    "machine learning specialization (andrew ng)": {
        "rating": 4.9,
        "total_reviews": 187000,
        "pros": "Lộ trình chuẩn mực, giải thích trực quan, bài lab chấm tự động.",
        "cons": "Cần biết Python cơ bản trước, tốc độ học khá nặng với người mất gốc.",
    },
    "google data analytics professional certificate": {
        "rating": 4.8,
        "total_reviews": 150000,
        "pros": "Bám sát công việc thực tế, có project cuối khóa để làm portfolio.",
        "cons": "Nội dung dàn trải, phải trả phí theo tháng nếu học chậm.",
    },
    "python for everybody specialization": {
        "rating": 4.8,
        "total_reviews": 220000,
        "pros": "Rất phù hợp người mất gốc, giảng viên kiên nhẫn, quiz sau mỗi bài.",
        "cons": "Chưa đi sâu vào lập trình hướng đối tượng và dự án lớn.",
    },
}

# 🚫 Từ khóa nhạy cảm: tool từ chối tra cứu ngay từ tầng công cụ (Test Case số 5)
BLOCKED_KEYWORDS = [
    "bom", "vũ khí", "vu khi", "chất nổ", "chat no", "thuốc nổ", "weapon", "bomb",
    "hack", "bẻ khóa", "be khoa", "crack", "đánh cắp tài khoản", "danh cap tai khoan",
    "ma túy", "ma tuy", "drug", "cờ bạc", "co bac", "lừa đảo", "lua dao",
]


def _is_blocked(text: str) -> bool:
    """
    Kiểm tra một chuỗi đầu vào có chứa từ khóa vi phạm chính sách an toàn hay không.

    Args:
        text (str): Nội dung người dùng muốn tra cứu.

    Returns:
        bool: True nếu phát hiện từ khóa bị cấm, ngược lại False.
    """
    lowered = str(text).lower()
    return any(keyword in lowered for keyword in BLOCKED_KEYWORDS)


def _clean_arg(value, param_name: str):
    """
    Chuẩn hóa tham số do Agent sinh ra trước khi tool xử lý.

    LLM thường sinh Action kiểu search_online_courses['Data Analysis'] hoặc để trống
    tham số, nên giá trị nhận được có thể là None, số, list... chứ không chắc là str.
    Hàm này ép về str sạch và chặn sớm các trường hợp rỗng.

    Args:
        value: Giá trị thô Agent truyền vào (có thể là bất kỳ kiểu nào).
        param_name (str): Tên tham số, dùng để in ra thông báo lỗi cho dễ hiểu.

    Returns:
        tuple[str | None, str | None]: (giá_trị_đã_sạch, thông_báo_lỗi).
            Nếu hợp lệ -> (chuỗi đã chuẩn hóa, None).
            Nếu không hợp lệ -> (None, chuỗi "LỖI: ...").
    """
    if value is None:
        return None, f"LỖI: Thiếu tham số '{param_name}'. Agent hãy gọi lại tool kèm tham số này."

    if not isinstance(value, str):
        # Không ép kiểu mù quáng: báo rõ để Agent sửa Action ở vòng lặp sau.
        try:
            value = str(value)
        except Exception:
            return None, f"LỖI: Tham số '{param_name}' có kiểu dữ liệu không hợp lệ."

    # Bỏ dấu nháy thừa mà LLM hay sinh ra: 'Data Analysis' hoặc "Data Analysis"
    cleaned = value.strip().strip("'\"").strip()
    if not cleaned:
        return None, f"LỖI: Tham số '{param_name}' đang rỗng. Hãy cho biết nội dung cần tra cứu."

    if len(cleaned) > 200:
        return None, f"LỖI: Tham số '{param_name}' quá dài (>200 ký tự). Hãy rút gọn từ khóa."

    return cleaned, None


def search_online_courses(topic: str) -> str:
    """
    Tra cứu danh sách khóa học trực tuyến đang có trên các nền tảng phổ biến
    (Coursera, Udemy, YouTube) theo chủ đề/từ khóa mà sinh viên yêu cầu.

    Khi nào Agent nên gọi tool này:
        - Người dùng hỏi "tìm khóa học về ...", "có khóa nào dạy ... không".
        - Cần thông tin thực tế: tên khóa, nền tảng, trình độ, thời lượng, học phí.
        - KHÔNG dùng cho câu hỏi tư vấn chung chung (lộ trình học, nên học ngôn ngữ nào).

    Args:
        topic (str): Chủ đề hoặc từ khóa cần tìm.
            Ví dụ: 'Data Analysis', 'Machine Learning', 'Python'.

    Returns:
        str: Danh sách khóa học tìm được, mỗi khóa gồm tên - nền tảng - trình độ -
            thời lượng - học phí. Nếu chủ đề vi phạm chính sách an toàn hoặc không
            có dữ liệu, trả về chuỗi bắt đầu bằng "TỪ CHỐI:" hoặc "LỖI:".
            Hàm KHÔNG BAO GIỜ raise Exception.

    Ví dụ:
        >>> search_online_courses("Data Analysis")
        'Tìm thấy 3 khóa học về "Data Analysis": ...'
    """
    try:
        topic, error = _clean_arg(topic, "topic")
        if error:
            return error

        if _is_blocked(topic):
            return (
                f"TỪ CHỐI: Yêu cầu tìm khóa học về '{topic}' vi phạm tiêu chuẩn cộng đồng "
                f"và quy định pháp luật. Tôi không thể tra cứu nội dung này. "
                f"Bạn có thể hỏi tôi về các khóa học lập trình, dữ liệu, ngoại ngữ..."
            )

        topic_lower = topic.lower()

        # Khớp gần đúng: 'khóa học Machine Learning cơ bản' vẫn khớp key 'machine learning'
        matched_key = None
        for key in COURSE_DB:
            if key in topic_lower or topic_lower in key:
                matched_key = key
                break

        if matched_key is None:
            available = ", ".join(COURSE_DB.keys())
            return (
                f"LỖI: Chưa có dữ liệu khóa học cho chủ đề '{topic}'. "
                f"Các chủ đề hiện có: {available}."
            )

        courses = COURSE_DB.get(matched_key) or []
        if not courses:
            return f"LỖI: Chủ đề '{topic}' tồn tại nhưng chưa có khóa học nào được cập nhật."

        lines = [f'Tìm thấy {len(courses)} khóa học về "{topic}":']
        for index, course in enumerate(courses, start=1):
            # Dùng .get() để thiếu field cũng không ném KeyError
            lines.append(
                f"{index}. {course.get('name', 'Không rõ tên')} "
                f"({course.get('platform', 'Không rõ nền tảng')}) "
                f"- Trình độ: {course.get('level', 'Đang cập nhật')} "
                f"- Thời lượng: {course.get('duration', 'Đang cập nhật')} "
                f"- Học phí: {course.get('price', 'Đang cập nhật')}"
            )
        return "\n".join(lines)

    except Exception as e:
        # Phanh cuối cùng: mọi lỗi ngoài dự đoán đều thành Observation, không làm sập app.
        return f"LỖI HỆ THỐNG khi tra cứu khóa học: {type(e).__name__} - {e}"


def get_course_reviews(course_name: str) -> str:
    """
    Tra cứu chất lượng của MỘT khóa học cụ thể: điểm số (số sao), số lượt đánh giá
    và nhận xét ưu/nhược điểm từ các học viên đi trước.

    Khi nào Agent nên gọi tool này:
        - Người dùng hỏi "khóa X đánh giá có tốt không", "khóa X bao nhiêu sao".
        - Thường được gọi SAU search_online_courses để chốt quyết định chọn khóa nào.

    Args:
        course_name (str): Tên chính xác (hoặc gần đúng) của khóa học.
            Ví dụ: 'Machine Learning for Everybody'.

    Returns:
        str: Điểm trung bình, tổng số lượt đánh giá, ưu điểm và nhược điểm của khóa học.
            Nếu không có dữ liệu review, trả về chuỗi bắt đầu bằng "LỖI:".
            Hàm KHÔNG BAO GIỜ raise Exception.

    Ví dụ:
        >>> get_course_reviews("Machine Learning for Everybody")
        'Đánh giá khóa học "Machine Learning for Everybody": ⭐ 4.7/5 ...'
    """
    try:
        course_name, error = _clean_arg(course_name, "course_name")
        if error:
            return error

        if _is_blocked(course_name):
            return (
                f"TỪ CHỐI: Không thể tra cứu đánh giá cho nội dung '{course_name}' "
                f"vì vi phạm tiêu chuẩn cộng đồng."
            )

        name_lower = course_name.lower()

        matched_key = None
        for key in REVIEW_DB:
            if key in name_lower or name_lower in key:
                matched_key = key
                break

        if matched_key is None:
            return (
                f"LỖI: Chưa có dữ liệu đánh giá cho khóa học '{course_name}'. "
                f"Hãy dùng search_online_courses để lấy đúng tên khóa học trước."
            )

        review = REVIEW_DB.get(matched_key) or {}

        # Số lượt đánh giá có thể thiếu hoặc không phải số -> format an toàn
        total = review.get("total_reviews")
        try:
            total_text = f"{int(total):,} lượt đánh giá"
        except (TypeError, ValueError):
            total_text = "chưa rõ số lượt đánh giá"

        return (
            f'Đánh giá khóa học "{course_name}":\n'
            f"- Điểm trung bình: ⭐ {review.get('rating', 'Đang cập nhật')}/5 ({total_text})\n"
            f"- Ưu điểm: {review.get('pros', 'Chưa có nhận xét.')}\n"
            f"- Nhược điểm: {review.get('cons', 'Chưa có nhận xét.')}"
        )

    except Exception as e:
        return f"LỖI HỆ THỐNG khi tra cứu đánh giá: {type(e).__name__} - {e}"


# ---------------------------------------------------------------------------
# 📖 TOOL SPECS - Mô tả chuẩn để Role 3 nhúng vào REACT_SYSTEM_PROMPT
# ---------------------------------------------------------------------------
TOOL_SPECS = [
    {
        "name": "search_online_courses",
        "description": (
            "Tra cứu danh sách khóa học trực tuyến (Coursera, Udemy, YouTube) "
            "theo chủ đề/từ khóa. Trả về tên khóa, nền tảng, trình độ, thời lượng, học phí."
        ),
        "parameters": {
            "topic": "str - Chủ đề cần tìm, ví dụ: 'Data Analysis', 'Machine Learning'."
        },
        "usage": "search_online_courses[Data Analysis]",
    },
    {
        "name": "get_course_reviews",
        "description": (
            "Tra cứu điểm đánh giá (số sao), số lượt đánh giá và nhận xét ưu/nhược điểm "
            "của học viên về MỘT khóa học cụ thể."
        ),
        "parameters": {
            "course_name": "str - Tên khóa học, ví dụ: 'Machine Learning for Everybody'."
        },
        "usage": "get_course_reviews[Machine Learning for Everybody]",
    },
]

# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "search_online_courses": search_online_courses,
    "get_course_reviews": get_course_reviews,
}


def call_tool(tool_name: str, tool_input: str) -> str:
    """
    Cửa ngõ an toàn để vòng lặp ReAct trong app.py gọi tool theo TÊN.

    LLM rất hay bịa ra tên tool không tồn tại (ví dụ: search_course, get_review),
    nếu app.py gọi thẳng AVAILABLE_TOOLS[name] sẽ dính KeyError và sập giữa vòng lặp.
    Hàm này bọc lại toàn bộ rủi ro đó và luôn trả về một chuỗi Observation hợp lệ.

    Args:
        tool_name (str): Tên tool Agent muốn gọi, ví dụ 'search_online_courses'.
        tool_input (str): Tham số Agent trích ra từ dòng Action.

    Returns:
        str: Kết quả của tool, hoặc chuỗi "LỖI: ..." nếu tên tool sai / tool gặp sự cố.
            Hàm KHÔNG BAO GIỜ raise Exception.
    """
    try:
        name = str(tool_name).strip()
        tool_func = AVAILABLE_TOOLS.get(name)

        if tool_func is None:
            available = ", ".join(AVAILABLE_TOOLS.keys())
            return (
                f"LỖI: Không tồn tại tool tên '{tool_name}'. "
                f"Chỉ được dùng các tool sau: {available}."
            )

        result = tool_func(tool_input)
        # Chốt chặn hợp đồng: Observation luôn phải là str
        return result if isinstance(result, str) else str(result)

    except Exception as e:
        return f"LỖI HỆ THỐNG khi thực thi tool '{tool_name}': {type(e).__name__} - {e}"
