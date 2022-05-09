from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from cms.fields import OrderField
from cms.mixins import GetAbsoluteUrl
from pathlib import Path
#from django.contrib.auth.models import User
import random
# from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth.models import Group


from django.utils import timezone


class TimeStamped(models.Model):
    creation_date = models.DateTimeField(editable=False)
    last_modified = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if not self.creation_date:
            self.creation_date = timezone.now()

        self.last_modified = timezone.now()
        return super(TimeStamped, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class Folder(TimeStamped):
    title = models.CharField(max_length=255, verbose_name='Folder')
    slug = models.SlugField(default="")
    order = OrderField(blank=True, verbose_name='Order #')
    # group = models.ForeignKey(Group, on_delete=models.CASCADE)
 
    def __str__(self):
        return self.title

    def save(self):
        self.slug =  slugify('{}'.format(self.title))
        return super().save()

    class Meta:
        db_table = 'folder'
        verbose_name = 'Folder'
        verbose_name_plural = "Folders"
        ordering = ('order', )

    # def get_absolute_url(self):
    #     return reverse("app:ticket-list", kwargs={"folder": self.id})
    def get_absolute_url(self):
        return reverse('app:folder-detail', kwargs={'pk': self.id})


class Ticket(TimeStamped):
    PENDING = 1
    CLOSED = 2
    CHOICES = (
        (PENDING, 'Pending'),
        (CLOSED, 'Closing'),
    )
    folder = models.ForeignKey(Folder, verbose_name='Folder', on_delete=models.CASCADE,null=False,blank=False)
    # user = models.ForeignKey(User,
    #                          verbose_name='User', on_delete=models.CASCADE)
    title = models.CharField(max_length=50, verbose_name='Title')
    date_sent = models.DateField(
        null=True, verbose_name='Date', help_text='YYYY-mm-dd')
    ticket_choices = models.PositiveSmallIntegerField(
        choices=CHOICES, default=PENDING, verbose_name='status')
    description = models.TextField(verbose_name="Content")
    order = OrderField(blank=True, verbose_name='Order #')
    waiting_for = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='waiting_for', blank=True,
                                    null=True, verbose_name='Waiting For', on_delete=models.CASCADE)
    sent_by = models.CharField(max_length=255, blank=True,
                               null=True, verbose_name="Sender")
    assigned_to = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         related_name='assigned_to',
                                         blank=True,
                                         verbose_name='Assigned')
   

    def __str__(self):
        return self.title

    def userassignment(self):
        return ",".join([str(p) for p in self.assigned_to.all()])

    def save(self, *args, **kwargs):
        # self.assignment = [str(p) for p in self.assigned_to.all()]
        super().save(*args, **kwargs)

    def get_fields(self):
        return [(field.verbose_name, field.value_from_object(self)) for field in self.__class__._meta.fields]

    # def get_absolute_url(self):
    #     return reverse("todo:task_detail", kwargs={"task_id": self.id})

    # @staticmethod
    # def get_products_by_id(ids):
    #     return Ticket.objects.filter(id__in=ids)

    # @staticmethod
    # def get_all_products():
    #     return Ticket.objects.all()

    # @staticmethod
    # def get_all_products_by_categoryid(folder_id):
    #     if folder_id:
    #         return Ticket.objects.filter(folder=folder_id)
    #     else:
    #         return Ticket.get_all_products()

    # def get_absolute_url(self):
    #    return reverse('app:ticket-update', kwargs={'pk': self.pk})

    class Meta:
        db_table = 'ticket'
        ordering = ['order']
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'

    def get_absolute_url(self):
        return reverse('app:ticket-list')


class Comment(TimeStamped):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, verbose_name='Ticket')
    slug = models.SlugField(max_length=255, verbose_name='Slug', unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             verbose_name='User', on_delete=models.CASCADE)
    comment = models.TextField(blank=False, null=False, verbose_name='Comment')
    order = OrderField(blank=True, for_fields=[
                       'ticket'], verbose_name='Order #')


    def __str__(self):
        return str(self.slug)

    def save(self, *args, **kwargs):
        self.slug = slugify('{}-{}'.format('F', random.random(),
                                           self.ticket.pk))
        super().save(*args, **kwargs)

    # def save_model(self, request, obj, form, change):
    #     obj.user = request.user
    #     super().save_model(request, obj, form, change)

    def get_absolute_url(self):
        return reverse("comment_detail", kwargs={"pk": self.pk})

    class Meta:
        db_table = 'comment'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ('order', 'last_modified')


class File(TimeStamped):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, verbose_name='Ticket')
    # user = models.ForeignKey(settings.AUTH_USER_MODEL,
    #                          verbose_name='User', on_delete=models.CASCADE)
    file = models.FileField(upload_to='files/', null=True,
                            blank=True, max_length=255, verbose_name='Filename')
    
    order = OrderField(blank=True, for_fields=[
                       'ticket'], verbose_name='Order #')

    @property
    def filename(self):
        return Path(self.file.name).name

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        if self.pk:
            old_file = File.objects.get(pk=self.pk).file
            if not old_file == self.file:
                storage = old_file.storage
                if storage.exists(old_file.name):
                    storage.delete(old_file.name)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        storage = self.file.storage
        if storage.exists(self.file.name):
            storage.delete(self.file.name)
        super().delete(*args, **kwargs)

    class Meta:
        db_table = 'file'
        verbose_name = 'File'
        verbose_name_plural = 'Files'
        ordering = ('order', )


































