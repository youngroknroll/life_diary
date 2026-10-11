from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from ..forms import (
    UserNoteForm,
)
from ..repositories import NoteRepository
from ..use_cases import (
    DeleteNoteUseCase,
    NoteData,
    SaveNoteUseCase,
)

_note_repo = NoteRepository()
_save_note = SaveNoteUseCase()
_delete_note = DeleteNoteUseCase()


def _note_data_from_form(form: UserNoteForm) -> NoteData:
    return NoteData(note=form.cleaned_data["note"])


@login_required
def usernote_list(request):
    notes = _note_repo.find_by_user(request.user)
    return render(request, "users/usernote_list.html", {"notes": notes})


@login_required
def usernote_create(request):
    if request.method == "POST":
        form = UserNoteForm(request.POST)
        if form.is_valid():
            _save_note.execute(_note_data_from_form(form), request.user)
            return redirect("users:usernote_list")
    else:
        form = UserNoteForm()
    return render(request, "users/usernote_form.html", {"form": form, "mode": "create"})


@login_required
def usernote_update(request, pk):
    note = _note_repo.get_or_404(pk, request.user)
    if request.method == "POST":
        form = UserNoteForm(request.POST, instance=note)
        if form.is_valid():
            _save_note.execute(_note_data_from_form(form), request.user, note_id=pk)
            return redirect("users:usernote_list")
    else:
        form = UserNoteForm(instance=note)
    return render(request, "users/usernote_form.html", {"form": form, "mode": "update"})


@login_required
@require_http_methods(["GET", "POST"])
def usernote_delete(request, pk):
    note = _note_repo.get_or_404(pk, request.user)
    if request.method == "POST":
        _delete_note.execute(request.user, pk)
        return redirect("users:usernote_list")
    return render(request, "users/usernote_confirm_delete.html", {"note": note})
