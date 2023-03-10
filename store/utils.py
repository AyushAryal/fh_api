def get_profile(model, user):
    if model.objects.filter(user=user.pk).exists():
        return model.objects.get(user=user.pk)
    return None
