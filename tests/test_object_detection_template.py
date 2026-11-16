import json
import unittest
from pathlib import Path
from zipfile import ZipFile


class TestObjectDetectionTemplate(unittest.TestCase):
    def test_new_app_output_datasets_have_empty_schemas_for_initialization(self):
        root = Path(__file__).resolve().parents[1] / 'apps'
        datasets_by_app = {
            'object-detection': ('object-labels', 'object-metadata'),
            'tabular-classification': ('tabular-labels', 'tabular-metadata', 'tabular-queries'),
            'text-labeling': ('text-labels', 'text-metadata'),
        }
        for app, datasets in datasets_by_app.items():
            with self.subTest(app=app), ZipFile(root / app / 'project.zip') as project:
                for dataset in datasets:
                    definition = json.loads(project.read('project_config/datasets/{}.json'.format(dataset)))
                    self.assertEqual(definition['schema']['columns'], [])

    def test_app_manifests_do_not_require_legacy_object_detection_plugins(self):
        root = Path(__file__).resolve().parents[1] / 'apps'
        for app in ('object-detection', 'tabular-classification', 'text-labeling'):
            with self.subTest(app=app), ZipFile(root / app / 'project.zip') as project:
                self.assertIsNone(project.testzip())
                manifest = json.loads(project.read('export-manifest.json'))
                plugins = {p['pluginId'] for p in manifest['exportedWithPlugins']}
                self.assertTrue(plugins.isdisjoint({'object-detection', 'object-detection-cpu', 'object-detection-gpu'}))

    def test_webapp_insights_and_authorizations_point_to_existing_webapps(self):
        root = Path(__file__).resolve().parents[1] / 'apps'
        for app in ('object-detection', 'tabular-classification', 'text-labeling'):
            with self.subTest(app=app), ZipFile(root / app / 'project.zip') as project:
                names = set(project.namelist())
                insights = [name for name in names if name.startswith('project_config/insights/') and name.endswith('.json')]
                for name in insights:
                    insight = json.loads(project.read(name))
                    if insight['type'] == 'web_app':
                        webapp = insight['params']['webAppSmartId']
                        self.assertIn('project_config/web_apps/{}.json'.format(webapp), names)
                params = json.loads(project.read('project_config/params.json'))
                for authorization in params.get('dashboardAuthorizations', {}).get('authorizations', []):
                    ref = authorization['objectRef']
                    if ref['objectType'] == 'WEB_APP':
                        self.assertIn('project_config/web_apps/{}.json'.format(ref['objectId']), names)

    def test_tabular_template_active_training_uses_project_environment(self):
        path = Path(__file__).resolve().parents[1] / 'apps/tabular-classification/project.zip'
        with ZipFile(path) as project:
            task = json.loads(project.read('project_config/analysis/pYCrBroE/ml/Uurvkg3v/params.json'))
            self.assertEqual(task['envSelection'], {'envMode': 'INHERIT'})
            manifest = json.loads(project.read('export-manifest.json'))
            self.assertNotIn('ml-assisted-labeling-visual-ml-python-36',
                             [ref.get('envName') for ref in manifest['usedCodeEnvRefs']])

    def test_template_configures_manual_labeling_without_legacy_detection_plugins(self):
        path = Path(__file__).resolve().parents[1] / 'apps/object-detection/project.zip'
        with ZipFile(path) as project:
            names = set(project.namelist())
            self.assertIsNone(project.testzip())
            self.assertNotIn('project_config/recipes/compute_object-queries.json', names)
            self.assertNotIn('project_config/scenarios/Retrain_model.json', names)
            self.assertNotIn('project_config/scenarios/Download_weights.json', names)
            self.assertIn('project_config/datasets/object-labels.json', names)
            self.assertIn('project_config/managed_folders/Sz5YxlDP.json', names)
            self.assertNotIn('project_config/managed_folders/eEvugZ8i.json', names)
            self.assertFalse(any(name.startswith('ipython_notebooks/.ipynb_checkpoints/') for name in names))
            for dataset in ('object-labels', 'object-metadata'):
                definition = json.loads(project.read('project_config/datasets/{}.json'.format(dataset)))
                self.assertEqual(definition['schema']['columns'], [])
            app = json.loads(project.read('project_config/app-manifest.json'))
            self.assertTrue(app['instanceFeatures']['showLabNavLink'])
            instructions = next(section['sectionText'] for section in app['homepageSections']
                                if section['sectionTitle'] == 'Running the experiment')
            self.assertIn('DeepHub object detection query sampler', instructions)
            self.assertIn('pause labeling', instructions)
            scenarios = {tile.get('scenarioId') for section in app['homepageSections'] for tile in section['tiles']}
            self.assertNotIn('Retrain_model', scenarios)
            self.assertNotIn('Download_weights', scenarios)
            self.assertIn('Restart_webapp', scenarios)
            self.assertIn('Refresh_deephub', scenarios)
            scenario = json.loads(project.read('project_config/scenarios/Refresh_deephub.json'))
            self.assertEqual(scenario['triggers'], [])
            steps = scenario['params']['steps']
            self.assertEqual([step['type'] for step in steps], ['custom_python', 'restart_webapp'])
            self.assertFalse(steps[0]['params']['proceedOnFailure'])
            self.assertIn('refresh_queries(', steps[0]['params']['script'])
            webapp = json.loads(project.read('project_config/web_apps/xFUUnCL.json'))
            self.assertNotIn('queries_ds', webapp['config'])
            self.assertEqual(webapp['config']['labels_ds'], 'object-labels')


if __name__ == '__main__':
    unittest.main()
