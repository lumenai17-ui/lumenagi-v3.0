"""Módulo para agrupar tareas por asignado."""

from typing import List, Dict, Any


def group_tasks_by_assignee(tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Agrupa una lista de tareas en un diccionario según el campo 'assigned_to'.

    Args:
        tasks: Lista de diccionarios donde cada diccionario representa una tarea
               y debe contener la clave 'assigned_to'.

    Returns:
        Dict[str, List[Dict]]: Diccionario donde las claves son los nombres de
        los asignados y los valores son listas de tareas asignadas a cada uno.

    Example:
        >>> tasks = [
        ...     {"id": 1, "title": "Fix bug", "assigned_to": "Alice"},
        ...     {"id": 2, "title": "Review PR", "assigned_to": "Bob"},
        ...     {"id": 3, "title": "Write tests", "assigned_to": "Alice"},
        ... ]
        >>> group_tasks_by_assignee(tasks)
        {'Alice': [{'id': 1, 'title': 'Fix bug', 'assigned_to': 'Alice'}, 
                   {'id': 3, 'title': 'Write tests', 'assigned_to': 'Alice'}], 
         'Bob': [{'id': 2, 'title': 'Review PR', 'assigned_to': 'Bob'}]}
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    
    for task in tasks:
        assignee = task.get("assigned_to")
        if assignee is not None:
            if assignee not in grouped:
                grouped[assignee] = []
            grouped[assignee].append(task)
    
    return grouped
