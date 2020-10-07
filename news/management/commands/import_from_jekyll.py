"""
One-time tool to move articles that are currently in
jekyll (written by hand) into articles in the db.

It separates the front-matter, where we were already storing
most of the 'Article' fields and the body, creating Article
entries.
"""
import re
import yaml
from django.core.management.base import BaseCommand
from news import models

# pylint: disable=missing-class-docstring


class Command(BaseCommand):
    help = "Imports legacy Jekyll posts in the form of articles"

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="+", type=str)

    def handle(self, *args, **options):

        for name in ["markus", "soseji"]:
            models.User.objects.get_or_create(
                username=name, email=f"{name}@gatillos.com", is_staff=True
            )

        for filename in options["files"]:
            with open(filename, "r") as source:
                # these files are a yaml document followed by '---' and a markdown body
                yaml_source = ""
                body_source = ""
                mode = None
                for line in source:
                    if line.startswith("---"):
                        if not mode:
                            mode = 1
                        elif mode == 1:
                            mode = 2
                    elif mode == 1:
                        yaml_source += line
                    elif mode == 2:
                        body_source += line

                data = yaml.load(yaml_source, Loader=yaml.SafeLoader)
                body_source = body_source.strip()

                target_url = data.get("target-url")
                if not target_url:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Ignoring {filename}: does not contain target_url"
                        )
                    )
                    continue

                if models.Article.objects.filter(target_url=target_url).exists():
                    self.stdout.write(
                        self.style.WARNING(f"Ignoring {filename}: url already exists")
                    )
                    continue

                # find user
                author: str = data.get("author", "markus")
                author_query = models.User.objects.filter(username=author)
                thumbnail = data.get("thumbnail", "/gfx/onlydognews-logo-main.png")
                date_created = data.get("date")
                if not date_created:
                    date_created = filename[0:10]

                # a couple of potential fixes
                # some dates are 2018-05-12T10:10:00+0100 and should be 2018-05-12T10:10:00+01:00
                regex = r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\+\d{2})(\d{2})$"
                if isinstance(date_created, str):
                    matches = re.match(regex, date_created)
                    if matches:
                        date_created = (
                            matches.group(1) + matches.group(2) + ":" + matches.group(3)
                        )

                print(
                    f"""
target_url={target_url}
moderated_submission=None
title={data.get("title")}
description={body_source}
thumbnail={thumbnail}
submitter={author}
approver=None
date_created={date_created}
"""
                )
                if not author_query.exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Ignoring {filename}: {author} does not exist"
                        )
                    )
                    continue
                author_user = author_query.first()
                article: models.Article = models.Article.objects.create(
                    target_url=target_url,
                    moderated_submission=None,
                    title=data.get("title"),
                    description=body_source,
                    thumbnail=thumbnail,
                    submitter=author_user,
                    approver=None,
                )
                article.date_created = date_created
                article.save()
                self.stdout.write(self.style.SUCCESS(f"Processed {filename}"))
