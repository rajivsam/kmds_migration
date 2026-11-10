import click
from .runner import SBAExperimentRunner


@click.group()
def cli():
    """KMDS SBA modeling pipeline CLI."""
    pass


@cli.command()
@click.option("--config", required=True, type=click.Path(exists=True), help="Path to SBA modeling config YAML")
@click.option("--export-dir", required=False, type=click.Path(), help="Optional output directory for serialized artifacts")
def run(config, export_dir):
    """Run the SBA modeling pipeline end-to-end."""
    runner = SBAExperimentRunner(config)
    train_df, validation_df, test_df, active_df = runner.prepare_datasets()
    train_df, validation_df, test_df, active_df = runner.transform_datasets(train_df, validation_df, test_df, active_df)
    results = runner.fit_and_calibrate(train_df, validation_df)
    test_results = runner.evaluate_test_set(test_df)
    active_results = runner.score_active_set(active_df)
    runner.export_artifacts(export_dir)

    click.echo("SBA modeling pipeline completed.")
    click.echo(results.to_string(index=False))
    if test_results is not None:
        click.echo("Test set evaluation (thresholded decision metrics):")
        click.echo(
            f"  pr_auc={test_results['pr_auc']:.4f}, "
            f"threshold={test_results['threshold']:.6f}, "
            f"balanced_accuracy={test_results['balanced_accuracy']:.4f}, "
            f"precision={test_results['precision']:.4f}, "
            f"recall={test_results['recall']:.4f}, "
            f"f2={test_results['f2']:.4f}, "
            f"brier_score={test_results['brier_score']:.4f}"
        )
    click.echo(f"Active set scored: {len(active_results)} rows")


if __name__ == '__main__':
    cli()
