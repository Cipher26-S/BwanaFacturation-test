from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "guide-pousser-code-github.pdf"


DOCUMENT = [
    ("title", "Guide debutant pour pousser un projet dans un repo GitHub"),
    ("p", "Ce document explique comment envoyer un projet local vers un depot GitHub, les problemes frequents, et comment les resoudre. L'exemple reprend le cas du projet BwanaFacturation."),

    ("h1", "1. Comprendre les mots importants"),
    ("p", "Git est l'outil qui garde l'historique du code sur ton ordinateur. GitHub est le site qui heberge ton depot en ligne. Un commit est une sauvegarde officielle. Un remote est l'adresse du depot en ligne, souvent appelee origin. Un push envoie tes commits vers GitHub."),

    ("h1", "2. Se placer dans le bon dossier"),
    ("p", "Avant toute commande, il faut entrer dans le dossier du projet. Dans notre cas, le vrai dossier Git etait gestion_devis_factures."),
    ("code", 'cd "C:\\Users\\USER\\Downloads\\Telegram Desktop\\Code_source_BwanaFacturation\\gestion_devis_factures"'),
    ("p", "Ensuite, on verifie que Git reconnait le projet."),
    ("code", "git status"),
    ("p", "Si Git affiche une branche comme main, tu es dans le bon depot. Si Git dit que ce n'est pas un depot Git, tu n'es pas dans le bon dossier ou le projet n'a pas encore ete initialise avec Git."),

    ("h1", "3. Verifier le depot GitHub configure"),
    ("p", "Pour voir ou ton projet va etre pousse, utilise cette commande :"),
    ("code", "git remote -v"),
    ("p", "Un resultat correct ressemble a ceci :"),
    ("code", "origin  https://github.com/bwanatechnologie-hub/BwanaFacturation.git (fetch)\norigin  https://github.com/bwanatechnologie-hub/BwanaFacturation.git (push)"),
    ("p", "Si l'adresse est mauvaise, on la remplace :"),
    ("code", "git remote set-url origin https://github.com/bwanatechnologie-hub/BwanaFacturation.git"),
    ("p", "Si aucun remote n'existe encore, on l'ajoute :"),
    ("code", "git remote add origin https://github.com/bwanatechnologie-hub/BwanaFacturation.git"),

    ("h1", "4. Verifier ce qui va etre envoye"),
    ("p", "Avant de pousser, regarde l'etat du projet :"),
    ("code", "git status --short --branch"),
    ("p", "S'il y a des fichiers modifies, il faut les ajouter puis creer un commit :"),
    ("code", 'git add .\ngit commit -m "Description courte des changements"'),
    ("warn", "Attention : git add . ajoute beaucoup de choses. Avant de l'utiliser, verifie que tu ne vas pas envoyer des secrets, un fichier .env, une base de donnees locale, des donnees clients, ou node_modules."),

    ("h1", "5. Pousser vers GitHub"),
    ("p", "La commande principale est :"),
    ("code", "git push -u origin main"),
    ("p", "Le -u dit a Git que ta branche locale main doit suivre la branche main sur GitHub. Apres ca, les prochains envois peuvent souvent se faire avec une commande plus courte :"),
    ("code", "git push"),

    ("h1", "6. Probleme : Git n'est pas reconnu"),
    ("p", "Erreur possible :"),
    ("code", "git : Le terme git n'est pas reconnu..."),
    ("p", "Cela veut dire que Git n'est pas installe ou n'est pas dans le PATH Windows."),
    ("p", "Solutions : installer Git pour Windows, fermer et rouvrir PowerShell, ou utiliser un git.exe deja installe ailleurs. Dans notre cas, Git existait dans Visual Studio Build Tools."),
    ("code", '& "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\BuildTools\\Common7\\IDE\\CommonExtensions\\Microsoft\\TeamFoundation\\Team Explorer\\Git\\cmd\\git.exe" status'),

    ("h1", "7. Probleme : mauvais repo GitHub"),
    ("p", "Erreur possible :"),
    ("code", "remote: Repository not found.\nfatal: repository 'https://github.com/ancien/repo.git/' not found"),
    ("p", "Cela veut dire que l'adresse du depot est mauvaise ou que ton compte n'a pas acces au depot."),
    ("p", "Solution : corriger le remote puis verifier :"),
    ("code", "git remote set-url origin https://github.com/bon-owner/bon-repo.git\ngit remote -v"),

    ("h1", "8. Probleme : mauvais compte GitHub"),
    ("p", "Erreur possible :"),
    ("code", "remote: Permission to owner/repo.git denied to AncienCompte.\nfatal: unable to access ... The requested URL returned error: 403"),
    ("p", "Cela veut dire que GitHub a reconnu un compte, mais ce compte n'a pas le droit d'ecrire dans le repo."),
    ("p", "Dans notre cas, Git utilisait Cipher6-sks alors que le collaborateur attendu etait Cipher26-S."),
    ("p", "Solutions : verifier que le bon compte est collaborateur avec permission Write, puis supprimer l'ancien identifiant GitHub memorise par Windows."),
    ("code", "cmdkey /list\ncmdkey /delete:git:https://github.com"),
    ("p", "Ensuite, relance le push. GitHub demandera une nouvelle connexion dans le navigateur."),
    ("code", "git push -u origin main"),
    ("note", "Important : user.name dans Git sert surtout a signer les commits. Le droit de pousser depend du compte GitHub authentifie."),

    ("h1", "9. Probleme : le repo distant contient deja quelque chose"),
    ("p", "Erreur possible :"),
    ("code", "! [rejected] main -> main (fetch first)\nerror: failed to push some refs\nhint: Updates were rejected because the remote contains work that you do not have locally."),
    ("p", "Cela veut dire que GitHub a deja un commit que ton ordinateur n'a pas."),
    ("p", "Solution propre : recuperer l'etat distant, regarder les differences, puis fusionner."),
    ("code", "git fetch origin\ngit log --oneline --decorate --graph --left-right main...origin/main"),
    ("p", "Si les deux historiques sont separes, on peut fusionner avec :"),
    ("code", 'git merge origin/main --allow-unrelated-histories -m "Fusion du depot distant initial"'),

    ("h1", "10. Probleme : conflit pendant le merge"),
    ("p", "Erreur possible :"),
    ("code", "CONFLICT (add/add): Merge conflict in README.md\nAutomatic merge failed; fix conflicts and then commit the result."),
    ("p", "Un conflit veut dire que Git ne sait pas quelle version garder."),
    ("p", "Pour garder ta version locale :"),
    ("code", "git checkout --ours README.md\ngit add README.md\ngit commit --no-edit"),
    ("p", "Pour garder la version GitHub :"),
    ("code", "git checkout --theirs README.md\ngit add README.md\ngit commit --no-edit"),
    ("p", "Apres le commit de fusion, on pousse a nouveau :"),
    ("code", "git push -u origin main"),

    ("h1", "11. Probleme : fichiers sensibles ou inutiles dans Git"),
    ("p", "Avant de pousser, verifie les fichiers suivis. Il faut eviter de publier .env, db.sqlite3, node_modules, mots de passe, tokens, donnees clients, utilisateurs, factures ou devis reels."),
    ("p", "Ajoute les fichiers a ignorer dans .gitignore :"),
    ("code", ".env\n*.env\ndb.sqlite3\nnode_modules/\nmedia/\n__pycache__/\n*.pyc"),
    ("p", "Si un fichier est deja suivi par Git, .gitignore ne suffit pas. Il faut le retirer du suivi sans le supprimer de ton ordinateur :"),
    ("code", "git rm --cached .env\ngit rm -r --cached node_modules\ngit add .gitignore\ngit commit -m \"Nettoyage des fichiers ignores\""),
    ("warn", "Si un secret a deja ete pousse sur GitHub, considere-le comme compromis. Change le mot de passe ou la cle, puis nettoie l'historique si necessaire."),

    ("h1", "12. Resume de notre cas BwanaFacturation"),
    ("p", "On a trouve le vrai dossier Git, corrige le remote vers bwanatechnologie-hub/BwanaFacturation, regle le probleme du mauvais compte GitHub, recupere le commit initial present sur GitHub, fusionne les historiques, resolu le conflit README.md, puis pousse main avec succes."),
    ("ok", "Resultat final : le projet local est synchronise avec GitHub, et main suit origin/main."),
]


def esc_pdf_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .encode("cp1252", errors="replace")
        .decode("cp1252")
    )


def wrap_text(text: str, width: int) -> list[str]:
    lines = []
    for raw in text.splitlines() or [""]:
        wrapped = textwrap.wrap(raw, width=width, break_long_words=False, replace_whitespace=False)
        lines.extend(wrapped or [""])
    return lines


def build_pages() -> list[list[tuple[str, int, str]]]:
    pages: list[list[tuple[str, int, str]]] = [[]]
    y = 800

    def new_page():
        nonlocal y
        pages.append([])
        y = 800

    def add_line(font: str, size: int, text: str, gap: int = 15):
        nonlocal y
        if y < 62:
            new_page()
        pages[-1].append((font, size, text))
        y -= gap

    for kind, text in DOCUMENT:
        if kind == "title":
            for line in wrap_text(text, 48):
                add_line("Helvetica-Bold", 22, line, 28)
            y -= 8
        elif kind == "h1":
            y -= 8
            for line in wrap_text(text, 62):
                add_line("Helvetica-Bold", 15, line, 22)
        elif kind == "code":
            y -= 4
            for line in wrap_text(text, 82):
                add_line("Courier", 9, line, 13)
            y -= 5
        elif kind in {"warn", "note", "ok"}:
            prefix = {"warn": "Attention : ", "note": "Note : ", "ok": "OK : "}[kind]
            for line in wrap_text(prefix + text, 78):
                add_line("Helvetica-Bold" if line.startswith(prefix) else "Helvetica", 10, line, 14)
            y -= 4
        else:
            for line in wrap_text(text, 86):
                add_line("Helvetica", 10, line, 14)
            y -= 3

    return pages


def page_stream(lines: list[tuple[str, int, str]], page_number: int) -> bytes:
    font_ids = {"Helvetica": "F1", "Helvetica-Bold": "F2", "Courier": "F3"}
    y = 800
    chunks = ["BT"]
    for font, size, text in lines:
        chunks.append(f"/{font_ids[font]} {size} Tf")
        chunks.append(f"54 {y} Td")
        chunks.append(f"({esc_pdf_text(text)}) Tj")
        chunks.append(f"-54 -{size + 4} Td")
        y -= size + 4
    chunks.append("/F1 8 Tf")
    chunks.append(f"500 32 Td")
    chunks.append(f"(Page {page_number}) Tj")
    chunks.append("ET")
    return ("\n".join(chunks)).encode("cp1252", errors="replace")


def write_pdf(output: Path):
    pages = build_pages()
    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"")
    font_helv_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    font_courier_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_ids = []
    for idx, lines in enumerate(pages, start=1):
        stream = page_stream(lines, idx)
        content_id = add_object(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
        page_obj = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> "
            + f"/Contents {content_id} 0 R >>".encode()
        )
        page_ids.append(add_object(page_obj))

    kids = b" ".join(f"{page_id} 0 R".encode() for page_id in page_ids)
    objects[pages_id - 1] = b"<< /Type /Pages /Kids [" + kids + b"] /Count " + str(len(page_ids)).encode() + b" >>"

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj_id, data in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{obj_id} 0 obj\n".encode())
        pdf.extend(data)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        b"trailer\n"
        + b"<< /Size "
        + str(len(objects) + 1).encode()
        + b" /Root "
        + str(catalog_id).encode()
        + b" 0 R >>\nstartxref\n"
        + str(xref_offset).encode()
        + b"\n%%EOF\n"
    )
    output.write_bytes(pdf)


if __name__ == "__main__":
    write_pdf(OUTPUT)
    print(OUTPUT)
