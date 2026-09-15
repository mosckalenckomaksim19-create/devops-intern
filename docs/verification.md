# Результаты проверки

Проверки выполнены 15 сентября 2026 года. Результаты стенда зафиксированы по выводу команд и изображению страницы, полученным при пошаговом выполнении задания.

## Окружение

| Компонент | Версия или конфигурация |
| --- | --- |
| WSL | 2.7.14.0 |
| Дистрибутив | Ubuntu-24.04, режим WSL2 |
| Docker Desktop | 4.91.0 |
| Docker Engine и CLI | 29.8.0, linux/amd64 |
| Python в Ubuntu | 3.12.3 |
| Python в образе | 3.12.14 |
| Kubernetes на узле | v1.37.0 |
| Профиль Minikube | devops-intern, один узел Ready |

Версия программы Minikube отдельно не зафиксирована; её можно получить командой `minikube version`.

## Docker и HTTP

- Проверочный контейнер `hello-world` успешно запущен.
- Собран образ `devops-hello:1.0.0`.
- Контейнер `devops-hello-local` запущен с пробросом `127.0.0.1:32777:32777`.
- `GET /` и `GET /healthz` вернули HTTP 200 как при запуске в Ubuntu, так и в контейнере.
- В контейнере `X-Instance` совпал с его коротким ID: `5067c87e4eeb`.
- Логи контейнера содержали успешные запросы к обоим адресам.
- Образ опубликован в [Docker Hub](https://hub.docker.com/r/xumuk595/devops-hello/tags) под тегом `1.0.0`.

Digest, возвращённый командой push:

```text
sha256:7e4bbcbaa1466daf2f4c221a41096f1aa3e9ba5fe838825c1d7386a8ef97d553
```

## Kubernetes

Серверная проверка обоих YAML через `kubectl apply --dry-run=server -f k8s/` прошла. После `kubectl apply -f k8s/` команда `rollout status` сообщила об успешном развёртывании.

Deployment `hello-world`: `READY 2/2`, `UP-TO-DATE 2`, `AVAILABLE 2`.

| Pod на момент проверки | IP | Готовность | Перезапуски |
| --- | --- | --- | --- |
| hello-world-69c945f78f-95s5k | 10.244.0.4 | Running, 1/1 | 0 |
| hello-world-69c945f78f-ttpnn | 10.244.0.3 | Running, 1/1 | 0 |

Service `hello-world` имеет тип ClusterIP и адрес `10.110.18.186:80`. EndpointSlice `hello-world-6hjzg` содержит оба адреса Pod с целевым портом 32777. Имена и адреса отражают конкретный запуск и могут измениться при пересоздании.

## Доступ к приложению

Страница `http://localhost:32777/` через port-forward показала `Hello world!` и `Instance: hello-world-69c945f78f-95s5k`.

Дополнительно из Pod выполнено 20 HTTP-запросов к `http://hello-world:80/` через Service:

```text
hello-world-69c945f78f-ttpnn: 11 requests
hello-world-69c945f78f-95s5k: 9 requests
```

Обе реплики обслуживают запросы через Service. Равномерное распределение в каждой серии не гарантируется. Port-forward выбирает один Pod; этот туннель сам по себе не доказывает балансировку Service.

## Дополнительные проверки файлов

При подготовке локально проверены ответ 404 для неизвестного пути, Content-Length и X-Instance. SQL-пример выполнен в SQLite: LEFT JOIN вернул пять строк, включая пользователя без заказов; HAVING вернул `user_id=1`, `total=1200`. XML draw.io и SVG разобраны, изображение схемы визуально проверено.

## Материалы

- [Схема draw.io](architecture.drawio)
- [Изображение схемы](architecture.png)
- [Каталог скриншотов](screenshots/)
- [GitHub-репозиторий](https://github.com/mosckalenckomaksim19-create/devops-intern)

Две реплики на одном узле не обеспечивают устойчивость к отказу самого узла. Проверки производительности и многoузловой отказоустойчивости не входили в это тестовое.
