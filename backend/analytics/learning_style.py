import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from django.utils import timezone
from datetime import timedelta
from .models import LearningEvent
from courses.models import CourseEnrollment

def cluster_learning_styles(course):
    now = timezone.now()
    recent_cutoff = now - timedelta(days=30)
    
    enrollments = CourseEnrollment.objects.filter(
        course=course, status=CourseEnrollment.Status.ACTIVE
    ).select_related("student__user")
    
    if not enrollments.exists():
        return {"error": "Không có sinh viên nào đăng ký khóa học này.", "clusters": []}
        
    students_data = []
    
    for enrollment in enrollments:
        events_30d = LearningEvent.objects.filter(
            student=enrollment.student,
            course=course,
            created_at__gte=recent_cutoff
        )
        
        total_events = events_30d.count()
        if total_events == 0:
            continue
            
        skips_fwd = events_30d.filter(event_type=LearningEvent.EventType.SKIP_FORWARD_10).count()
        skips_bwd = events_30d.filter(event_type=LearningEvent.EventType.SKIP_BACKWARD_10).count()
        notes = events_30d.filter(
            event_type__in=[
                LearningEvent.EventType.NOTE_CREATED,
                LearningEvent.EventType.NOTE_UPDATED,
                LearningEvent.EventType.NOTE_DELETED,
            ]
        ).count()
        
        rates = [e.playback_rate for e in events_30d if e.playback_rate is not None]
        avg_playback_rate = sum(rates) / len(rates) if rates else 1.0
        
        f1 = skips_fwd / total_events
        f2 = skips_bwd / total_events
        f3 = notes / total_events
        f4 = avg_playback_rate
        f5 = enrollment.course_progress_percent / 100.0
        f6 = total_events / 30.0
        
        students_data.append({
            "student_id": enrollment.student.user_id,
            "student_name": enrollment.student.user.full_name,
            "features": [f1, f2, f3, f4, f5, f6]
        })
        
    if len(students_data) < 4:
        # Not enough data to cluster
        return {
            "error": "Cần ít nhất 4 sinh viên có dữ liệu hoạt động để phân tích nhóm học.",
            "clusters": []
        }
        
    # Prepare matrix X
    X = np.array([d["features"] for d in students_data])
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    k = min(4, len(students_data))
    # Dùng n_init='auto' để không báo warning
    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
    clusters = kmeans.fit_predict(X_scaled)
    
    # Analyze centroids to assign labels
    # centroids shape: (k, 6)
    centroids_unscaled = scaler.inverse_transform(kmeans.cluster_centers_)
    
    cluster_labels = {}
    for i in range(k):
        centroid = centroids_unscaled[i]
        f1_skip_fwd = centroid[0]
        f2_skip_bwd = centroid[1]
        f3_note = centroid[2]
        f4_rate = centroid[3]
        f5_prog = centroid[4]
        f6_freq = centroid[5]
        
        if f3_note > 0.05 and f2_skip_bwd > 0.05:
            style_name = "Deep Learner"
            icon = "🎓"
            description = "Học chậm, ghi chú nhiều và thường xuyên xem lại."
        elif f4_rate > 1.1 and f5_prog > 0.5:
            style_name = "Speed Runner"
            icon = "⚡"
            description = "Xem video tốc độ nhanh, hoàn thành khóa học sớm."
        elif f2_skip_bwd > 0.1 and f5_prog < 0.5:
            style_name = "Struggling Learner"
            icon = "⚠️"
            description = "Hay phải tua lại video, tiến độ hoàn thành chậm."
        else:
            style_name = "Passive Viewer"
            icon = "😴"
            description = "Ít tương tác, học theo tiến độ bình thường."
            
        cluster_labels[i] = {
            "style_name": style_name,
            "icon": icon,
            "description": description
        }
        
    # Group students by cluster
    cluster_groups = {i: [] for i in range(k)}
    for idx, student_info in enumerate(students_data):
        cluster_idx = clusters[idx]
        cluster_groups[cluster_idx].append({
            "student_id": str(student_info["student_id"]),
            "student_name": student_info["student_name"]
        })
        
    results = []
    for i in range(k):
        results.append({
            "cluster_id": i,
            "style_name": cluster_labels[i]["style_name"],
            "icon": cluster_labels[i]["icon"],
            "description": cluster_labels[i]["description"],
            "count": len(cluster_groups[i]),
            "students": cluster_groups[i]
        })
        
    # Sort results by size
    results.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "course_id": course.course_id,
        "course_name": course.course_name,
        "total_students": len(students_data),
        "clusters": results
    }
