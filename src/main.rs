use serde::Deserialize;
use actix_web::middleware::Logger;
use actix_web::{web, App, HttpRequest, HttpServer, Responder, HttpResponse, get, post};
use sha2::Digest;
use tokio::process::Command;
use tokio::time::timeout;
use std::time::Duration;
use askama::Template;

#[get("/v/{hash}")]
async fn view_hash(req: HttpRequest) -> impl Responder {
    let hash = req.match_info().get("hash").expect("No hash given");
    return root(hash).await;
}

#[get("/robots.txt")]
async fn robots(_req: HttpRequest) -> impl Responder {
    return "User-agent: *\nDisallow: /\n"
}

#[derive(Template)]
#[template(path = "base.html")]
struct RootTemplate<'a> {
    imghash: &'a str,
}

async fn root(hash: &str) -> impl Responder {
    let template = RootTemplate {
        imghash: hash,
    };

    return match template.render() {
        Ok(html) => HttpResponse::Ok().content_type("text/html").body(html),
        Err(_) => HttpResponse::BadRequest().body("what are you doing mate"),
    };
}

#[get("/")]
async fn home(_req: HttpRequest) -> impl Responder {
    return root("raw").await;
}

#[derive(Deserialize)]
struct PostData {
    text: String,
}

#[post("/post")]
async fn post(mut form: web::Form<PostData>) -> impl Responder {
    form.text.truncate(100);

    if form.text.is_empty() || !form.text.is_ascii() {
        return HttpResponse::BadRequest().finish();
    }

    let mut sha_builder = sha2::Sha256::new();
    sha_builder.update(form.text.as_bytes());
    let hash = hex::encode(sha_builder.finalize().as_slice());

    let path = std::path::Path::new("memes").join(hash.to_owned() + ".jpg");
    if path.exists() {
        return HttpResponse::Ok().body(hash);
    }

    let mut make_meme_fut = Command::new("convert").arg("memes/raw.jpg")
        .arg("-font").arg("Impact")
        .arg("-fill").arg("white")
        .arg("-stroke").arg("black")
        .arg("-strokewidth").arg("2")
        .arg("-background").arg("none")
        .arg("-gravity").arg("south")
        .arg("-pointsize").arg("120")
        .arg("-size").arg("788x")
        .arg("caption:".to_owned() + &form.text)
        .arg("-composite")
        .arg(path)
        .spawn()
        .expect("Oooo no meme :(");

    if let Err(_) = timeout(Duration::from_secs(1), make_meme_fut.wait()).await {
        return HttpResponse::Ok().body("welp too slow");
    }

    return HttpResponse::Ok().body(hash);
}

#[actix_rt::main]
async fn main() -> std::io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let server = args.get(1).expect("no hostname given");
    let port = args.get(2).expect("no port given");

    std::env::set_var("RUST_LOG", "info");
    env_logger::init();

    HttpServer::new(|| {
        App::new()
            .wrap(Logger::default())
            .service(view_hash)
            .service(post)
            .service(home)
            .service(robots)
            .service(actix_files::Files::new("memes", "memes"))
    })
    .bind(format!("{}:{}", server, port))?
    .run()
    .await
}