using DemoApp.Services;
using DemoApp.ViewModels;
using DesignData.SDS2;
using DesignData.SDS2.Database;
using DesignData.SDS2.HybridPlugins.Communication;
using DesignData.SDS2.HybridPlugins.Services;
using Microsoft.Extensions.DependencyInjection;
using SDS2.Plugin.UI.Themes;
using System;
using System.Collections.Generic;
using System.Configuration;
using System.Data;
using System.Linq;
using System.Threading.Tasks;
using System.Transactions;
using System.Windows;
using System.Windows.Threading;
using Transaction = DesignData.SDS2.Database.Transaction;

namespace DemoApp
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        private bool _linkedToSDS2 = false;
        private ServiceProvider _serviceProvider;
        private SDS2Connect _sds2Connect;

        public App()
        {
            _linkedToSDS2 = Linker.Link(MajorVersion.TwentyTwentyThree);

            DispatcherUnhandledException += App_DispatcherUnhandledException;
            Application.Current.Exit += Current_Exit;

            ServiceCollection services = new ServiceCollection();
            ConfigureServices(services);
            _serviceProvider = services.BuildServiceProvider();
        }

        private void Current_Exit(object sender, ExitEventArgs e)
        {
            if (_sds2Connect is not null)
            {
                _sds2Connect.Dispose();
            }
        }

        private void App_DispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
        {
            if (_sds2Connect is not null)
            {
                _sds2Connect.Dispose();
            }
        }

        private void ConfigureServices(ServiceCollection services)
        {
            services.AddSingleton(new SDS2InfoService(_linkedToSDS2));
            _sds2Connect = new SDS2Connect();
            services.AddSingleton(_sds2Connect);
            services.AddTransient<SetupSerializer>();
            services.AddSingleton<MainWindow>();
            services.AddSingleton<MainWindowViewModel>();
            services.AddSingleton<AppState>();
        }

        private void Application_Startup(object sender, StartupEventArgs e)
        {
            string jobName = string.Empty;
            Themes theme = Themes.Dark;

            foreach (string arg in e.Args)
            {
                string[] parts = arg.Split(':');

                switch (parts[0])
                {
                    case "jobName":
                        jobName = parts[1];
                        break;

                    case "theme":
                        theme = (Themes)Enum.Parse(typeof(Themes), parts[1]);
                        break;
                }
            }

            SDS2InfoService sds2InfoService = _serviceProvider.GetService<SDS2InfoService>();

            if (!string.IsNullOrEmpty(jobName))
            {
                sds2InfoService.OpenJob(jobName);
            }
            else
            {
                sds2InfoService.OpenJob();
            }

            // Uncomment to connect to the Python SDS2 Plugin
            // This is thread blocking
            _sds2Connect.Connect(sds2InfoService.Job);
            
            //This a temp fix issue where the job seems to be null at a later point in time
            //When another readonly transaction is created
            using ReadOnlyTransaction action = new ReadOnlyTransaction(sds2InfoService.Job);

            _serviceProvider.GetService<AppState>().Theme = theme;

            _serviceProvider.GetService<MainWindow>().ShowDialog();

        }
    }
}
