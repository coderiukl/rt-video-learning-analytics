import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from courses.models import Course, CourseEnrollment

def build_course_interaction_matrix():
    """
    Build student-course interaction matrix based on enrollment progress.
    """
    enrollments = CourseEnrollment.objects.values('student_id', 'course_id', 'course_progress_percent')
    
    if not enrollments:
        return None, {}, {}

    student_idx = {}
    course_idx = {}
    
    for row in enrollments:
        s_id = row['student_id']
        c_id = row['course_id']
        if s_id not in student_idx:
            student_idx[s_id] = len(student_idx)
        if c_id not in course_idx:
            course_idx[c_id] = len(course_idx)
            
    num_students = len(student_idx)
    num_courses = len(course_idx)
    
    M = np.zeros((num_students, num_courses))
    
    for row in enrollments:
        progress = row['course_progress_percent'] or 0.0
        signal = min(progress / 100.0, 1.0)
        if signal == 0:
            signal = 0.1 # Interaction noted
        
        s_i = student_idx[row['student_id']]
        c_i = course_idx[row['course_id']]
        M[s_i, c_i] = signal
        
    return M, student_idx, course_idx

def get_similar_courses(course_id, M, course_idx, n=5):
    if M is None or course_id not in course_idx:
        return []
        
    num_students = M.shape[0]
    num_courses = M.shape[1]
    
    if num_students < 3 or num_courses < 3:
        return []
        
    n_components = min(20, num_students - 1)
    if n_components < 1:
        return []
        
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    try:
        M_T = M.T
        item_factors = svd.fit_transform(M_T)
        
        sim_matrix = cosine_similarity(item_factors)
        
        c_i = course_idx[course_id]
        sim_scores = sim_matrix[c_i]
        
        sorted_indices = np.argsort(sim_scores)[::-1]
        
        idx_to_course = {idx: c_id for c_id, idx in course_idx.items()}
        
        similar_courses = []
        for idx in sorted_indices:
            if idx == c_i:
                continue
            similar_courses.append({
                "course_id": idx_to_course[idx],
                "similarity_score": float(sim_scores[idx])
            })
            if len(similar_courses) >= n:
                break
                
        return similar_courses
    except Exception as e:
        print(f"SVD Error: {e}")
        return []

def recommend_courses_for_student(student, current_course_id, n=3):
    M, student_idx, course_idx = build_course_interaction_matrix()
    
    similar_courses = get_similar_courses(current_course_id, M, course_idx, n=10)
    
    enrolled_course_ids = set()
    if student:
        enrolled_course_ids = set(
            CourseEnrollment.objects.filter(student=student).values_list('course_id', flat=True)
        )
    
    recommendations = []
    for sc in similar_courses:
        c_id = sc['course_id']
        if c_id not in enrolled_course_ids and c_id != current_course_id:
            try:
                course = Course.objects.select_related('instructor__user').get(course_id=c_id, status=Course.Status.PUBLISHED)
                recommendations.append({
                    "course_id": course.course_id,
                    "course_name": course.course_name,
                    "instructor_name": course.instructor.user.full_name,
                    "similarity_score": sc["similarity_score"]
                })
                if len(recommendations) >= n:
                    break
            except Course.DoesNotExist:
                continue
                
    if len(recommendations) < n:
        fallback_courses = Course.objects.select_related('instructor__user').filter(
            status=Course.Status.PUBLISHED
        ).exclude(
            course_id__in=enrolled_course_ids
        ).exclude(
            course_id=current_course_id
        ).order_by('-created_at')
        
        rec_ids = {r["course_id"] for r in recommendations}
        for fc in fallback_courses:
            if fc.course_id not in rec_ids:
                recommendations.append({
                    "course_id": fc.course_id,
                    "course_name": fc.course_name,
                    "instructor_name": fc.instructor.user.full_name,
                    "similarity_score": 0.0
                })
                rec_ids.add(fc.course_id)
                if len(recommendations) >= n:
                    break
                    
    return recommendations

def recommend_courses_for_student_global(student, n=5):
    """
    Recommend courses based on ALL courses the student is currently enrolled in.
    Aggregates similarity scores across all enrolled courses.
    """
    if not student:
        return []
        
    enrolled_course_ids = list(CourseEnrollment.objects.filter(student=student).values_list('course_id', flat=True))
    
    # Fallback if student hasn't enrolled in anything
    if not enrolled_course_ids:
        fallback_courses = Course.objects.select_related('instructor__user').filter(
            status=Course.Status.PUBLISHED
        ).order_by('-created_at')[:n]
        return [{
            "course_id": fc.course_id,
            "course_name": fc.course_name,
            "instructor_name": fc.instructor.user.full_name,
            "similarity_score": 0.0
        } for fc in fallback_courses]
        
    M, student_idx, course_idx = build_course_interaction_matrix()
    if M is None:
        return []
        
    aggregated_scores = {}
    
    for c_id in enrolled_course_ids:
        similar_courses = get_similar_courses(c_id, M, course_idx, n=15)
        for sc in similar_courses:
            rec_c_id = sc['course_id']
            if rec_c_id in enrolled_course_ids:
                continue
            # Accumulate scores. We use max to avoid favoring courses just because they are slightly similar to many things
            # Alternatively, sum can be used to favor courses similar to MULTIPLE enrolled courses. We use sum.
            if rec_c_id not in aggregated_scores:
                aggregated_scores[rec_c_id] = 0.0
            aggregated_scores[rec_c_id] += sc['similarity_score']
            
    # Sort by aggregated score
    sorted_rec_ids = sorted(aggregated_scores.items(), key=lambda item: item[1], reverse=True)[:n]
    
    recommendations = []
    for rec_c_id, score in sorted_rec_ids:
        try:
            course = Course.objects.select_related('instructor__user').get(course_id=rec_c_id, status=Course.Status.PUBLISHED)
            recommendations.append({
                "course_id": course.course_id,
                "course_name": course.course_name,
                "instructor_name": course.instructor.user.full_name,
                "similarity_score": score
            })
        except Course.DoesNotExist:
            continue
            
    # Fallback to fill up n if necessary
    if len(recommendations) < n:
        rec_ids = {r["course_id"] for r in recommendations}
        fallback_courses = Course.objects.select_related('instructor__user').filter(
            status=Course.Status.PUBLISHED
        ).exclude(
            course_id__in=enrolled_course_ids
        ).order_by('-created_at')
        
        for fc in fallback_courses:
            if fc.course_id not in rec_ids:
                recommendations.append({
                    "course_id": fc.course_id,
                    "course_name": fc.course_name,
                    "instructor_name": fc.instructor.user.full_name,
                    "similarity_score": 0.0
                })
                rec_ids.add(fc.course_id)
                if len(recommendations) >= n:
                    break
                    
    return recommendations
