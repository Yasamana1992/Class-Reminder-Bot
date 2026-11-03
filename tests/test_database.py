import pytest
import database


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"

    monkeypatch.setattr(database, "DB_NAME", str(db_file))

    database.create_admins_table()
    database.create_students_table()
    database.add_student_link_columns()
    database.create_classes_table()
    database.create_class_schedules_table()
    database.create_student_classes_table()

    return db_file


def test_add_student_success(test_db):
    result = database.add_student("Sara Ahmadi", "09123456789")

    assert result is True

    students = database.get_students()

    assert len(students) == 1
    assert students[0][1] == "Sara Ahmadi"


def test_add_student_strips_whitespace(test_db):
    database.add_student("  Sara Ahmadi  ")

    students = database.get_students()

    assert students[0][1] == "Sara Ahmadi"


def test_add_student_rejects_empty_name(test_db):
    with pytest.raises(ValueError):
        database.add_student("   ")


def test_add_student_rejects_duplicate_telegram_id(test_db):
    first_result = database.add_student(
        "Sara Ahmadi",
        "09123456789",
        123456
    )

    second_result = database.add_student(
        "Ali Ahmadi",
        "09123456788",
        123456
    )

    assert first_result is True
    assert second_result is False

    students = database.get_students()


def test_delete_student_success(test_db):
    database.add_student("Sara Ahmadi")

    student_id = database.get_students()[0][0]

    result = database.delete_student(student_id)

    assert result is True
    assert database.get_students() == []


def test_delete_nonexistent_student(test_db):
    result = database.delete_student(999)

    assert result is False


def test_add_admin_success(test_db):
    result = database.add_admin(12345, "admin")

    assert result is True
    assert database.get_admin_role(12345) == "admin"


def test_add_duplicate_admin(test_db):
    database.add_admin(12345, "admin")

    result = database.add_admin(12345, "admin")

    assert result is False
    assert database.get_admin_role(12345) == "admin"


def test_enroll_student_success(test_db):
    database.add_student("Sara Ahmadi")
    student_id = database.get_students()[0][0]

    class_id = database.add_class("Python")

    result = database.enroll_student(student_id, class_id)

    assert result is True
    assert database.get_student_classes(student_id) == [
        (class_id, "Python")
    ]


def test_enroll_student_twice(test_db):
    database.add_student("Sara Ahmadi")
    student_id = database.get_students()[0][0]

    class_id = database.add_class("Python")

    first_result = database.enroll_student(student_id, class_id)
    second_result = database.enroll_student(student_id, class_id)

    assert first_result is True
    assert second_result is False
    assert len(database.get_student_classes(student_id)) == 1


def test_delete_student_removes_enrollments(test_db):
    database.add_student("Sara Ahmadi")
    student_id = database.get_students()[0][0]

    class_id = database.add_class("Python")
    database.enroll_student(student_id, class_id)

    result = database.delete_student(student_id)

    assert result is True
    assert database.get_student_classes(student_id) == []


def test_remove_admin_success(test_db):
    database.add_admin(12345, "admin")

    result = database.remove_admin(12345)

    assert result is True
    assert database.get_admin_role(12345) is None


def test_remove_owner_is_not_allowed(test_db):
    database.add_admin(12345, "owner")

    result = database.remove_admin(12345)

    assert result is False
    assert database.get_admin_role(12345) == "owner"


def test_add_class_schedule_success(test_db):
    class_id = database.add_class("Python")

    result = database.add_class_schedule(
        class_id, 0, "10:00", "12:00"
    )

    schedules = database.get_class_schedules(class_id)

    assert result > 0
    assert len(schedules) == 1
    assert schedules[0][1:] == (0, "10:00", "12:00")


def test_add_class_schedule_rejects_invalid_time(test_db):
    class_id = database.add_class("Python")

    with pytest.raises(ValueError):
        database.add_class_schedule(
            class_id, 0, "12:00", "10:00"
        )


def test_unlink_student_telegram(test_db):
    database.add_student("Sara Ahmadi", telegram_id=123456)

    student_id = database.get_students()[0][0]

    result = database.unlink_student_telegram(student_id)

    assert result is True

    students = database.get_students()
    assert students[0][3] is None