# database.py
from typing import Dict, List
from datetime import date

class InMemoryDB:
    def __init__(self):
        self.students: Dict[str, Dict] = {}  # student_id -> {id, student_id, name}
        self.attendance: Dict[str, Dict[str, str]] = {}  # date -> {student_id -> status}
        self.next_student_id = 1
    
    def add_student(self, student_id: str, name: str) -> bool:
        if student_id in self.students:
            return False
        
        self.students[student_id] = {
            "id": self.next_student_id,
            "student_id": student_id,
            "name": name
        }
        self.next_student_id += 1
        return True
    
    def get_student(self, student_id: str) -> Dict | None:
        return self.students.get(student_id)
    
    def get_all_students(self) -> List[Dict]:
        return list(self.students.values())
    
    def mark_absences(self, date_str: str, absent_student_ids: List[str]) -> Dict:
        if date_str not in self.attendance:
            self.attendance[date_str] = {}
        
        # Reset all students to present for this date
        for student_id in self.students:
            self.attendance[date_str][student_id] = "present"
        
        # Mark specified students as absent
        absent_students = []
        for student_id in absent_student_ids:
            if student_id in self.students:
                self.attendance[date_str][student_id] = "absent"
                absent_students.append({
                    "student_id": student_id,
                    "name": self.students[student_id]["name"]
                })
        
        return {
            "date": date_str,
            "total_students": len(self.students),
            "present_count": len(self.students) - len(absent_students),
            "absent_count": len(absent_students),
            "absent_students": absent_students
        }
    
    def get_attendance(self, date_str: str) -> Dict:
        if date_str not in self.attendance:
            return {
                "date": date_str,
                "total_students": len(self.students),
                "present_count": len(self.students),
                "absent_count": 0,
                "absent_students": []
            }
        
        absent_students = []
        for student_id, status in self.attendance[date_str].items():
            if status == "absent" and student_id in self.students:
                absent_students.append({
                    "student_id": student_id,
                    "name": self.students[student_id]["name"]
                })
        
        return {
            "date": date_str,
            "total_students": len(self.students),
            "present_count": len(self.students) - len(absent_students),
            "absent_count": len(absent_students),
            "absent_students": absent_students
        }
    
    def get_monthly_report(self, year: int, month: int) -> Dict:
        month_pattern = f"{year}-{month:02d}-"
        
        dates_with_absences = [
            date_str for date_str in self.attendance 
            if date_str.startswith(month_pattern) 
            and any(status == "absent" for status in self.attendance[date_str].values())
        ]
        dates_with_absences.sort()
        
        student_absences = []
        for student_id, student in self.students.items():
            absence_count = sum(
                1 for date_str in self.attendance 
                if date_str.startswith(month_pattern) 
                and self.attendance[date_str].get(student_id) == "absent"
            )
            student_absences.append({
                "student_id": student_id,
                "name": student["name"],
                "absence_count": absence_count
            })
        
        student_absences.sort(key=lambda x: x["absence_count"], reverse=True)
        
        daily_absences = {
            date_str: sum(1 for status in self.attendance[date_str].values() if status == "absent")
            for date_str in self.attendance
            if date_str.startswith(month_pattern) 
            and sum(1 for status in self.attendance[date_str].values() if status == "absent") > 0
        }
        
        return {
            "year": year,
            "month": month,
            "total_students": len(self.students),
            "dates_with_absences": dates_with_absences,
            "student_absence_summary": student_absences,
            "daily_absence_counts": daily_absences
        }

# Initialize the database instance
db = InMemoryDB()