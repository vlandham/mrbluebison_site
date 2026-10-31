# mrbluebison.com

## Publishing

The site is built with Jekyll using GitHub's official Pages build action.
The workflow in `.github/workflows/pages.yml` builds pull requests without
deploying them, and builds and deploys pushes to `gh-pages`. The branch keeps
its existing name, but publishing uses an Actions artifact rather than
GitHub Pages' legacy branch build.

To activate the workflow after merging it, open **Settings > Pages** and
select **GitHub Actions** under **Build and deployment > Source**. Then run
**Deploy site to GitHub Pages** from the **Actions** tab, or push a new commit
to `gh-pages`.

Keep the custom domain set to `mrbluebison.com` in **Settings > Pages**.
Actions publishing uses that setting, not the repository's `CNAME` file.
No Namecheap DNS changes are needed for this migration. Enable **Enforce
HTTPS** in Pages settings once GitHub has provisioned the certificate.

The workflow uses the GitHub Pages Jekyll environment, matching the hosted
build instead of installing the legacy dependencies in `Gemfile.lock`.