from channels import Group
from aristotle_mdr import models as MDR
from aristotle_mdr import messages


def safe_object(message):
    __object__ = message['__object__']
    if __object__.get('object', None):
        instance = __object__['object']
    else:
        model = apps.get_model(__object__['app_label'], __object__['model_name'])
        instance = model.objects.filter(pk=__object__['pk']).first()
    return instance


def concept_saved(message):
    instance = safe_object(message)
    if not instance:
        return

    for p in instance.favourited_by.all():
        messages.favourite_updated(recipient=p.user, obj=instance)
    if instance.workgroup:
        for user in instance.workgroup.viewers.all():
            if message['created']:
                messages.workgroup_item_new(recipient=user, obj=instance)
            else:
                messages.workgroup_item_updated(recipient=user, obj=instance)
    try:
        # This will fail during first load, and if admins delete aristotle.
        system = User.objects.get(username="aristotle")
        for post in instance.relatedDiscussions.all():
            DiscussionComment.objects.create(
                post=post,
                body='The item "{name}" (id:{iid}) has been changed.\n\n\
                    <a href="{url}">View it on the main site.</a>.'.format(
                    name=instance.name,
                    iid=instance.id,
                    url=reverse("aristotle:item", args=[instance.id])
                ),
                author=system,
            )
    except:
        pass


def new_comment_created(message, **kwargs):
    comment = safe_object(message)
    if comment:
        messages.new_comment_created(comment)


def new_post_created(message, **kwargs):
    post = safe_object(message)

    if post:
        for user in post.workgroup.members.all():
            if user != post.author:
                messages.new_post_created(post, user)