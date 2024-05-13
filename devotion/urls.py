"""
URL configuration for devotion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
import users.views as users
import projects.views as projects
import tasks.views as tasks
import dashboards.views as dashboards

urlpatterns = [
    path("admin/", admin.site.urls),

    path("login/", TokenObtainPairView.as_view()),
    path("login/refresh/", TokenRefreshView.as_view()),
    path("test/", users.test),
    path("users/", users.UsersView.as_view()),
    path("me/", users.CurrentUserView.as_view()),
    path("me/projects/", users.get_current_user_projects),

    path("projects/", projects.create_project),
    path("projects/<uuid:project_id>/", projects.ProjectView.as_view()),
    path("projects/<uuid:project_id>/subtasks/", projects.get_all_subtree_tasks),
    path("projects/<uuid:project_id>/members/", projects.get_project_members),

    path("tasks/", tasks.create_task),
    path("tasks/<uuid:task_id>/", tasks.TaskView.as_view()),
    path("tasks/<uuid:task_id>/status/", tasks.update_task_status),
    path("tasks/<uuid:task_id>/subtasks/", tasks.get_all_subtree_tasks),

    path("dashboards/<uuid:project_id>/", dashboards.DashboardView.as_view()),
    path("widgets/", dashboards.create_widget),
    # path("widgets/<uuid:widget_id>/", dashboards.WidgetView.as_view()),
    path("all_widgets/", dashboards.get_all_widgets),

    path("data_sources/", dashboards.create_data_source),
    path("data_sources/<uuid:data_source_id>/", dashboards.DataSourceView.as_view()),
    path("all_data_sources/", dashboards.get_all_data_sources),
]
