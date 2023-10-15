using DemoApp.Commands;
using DemoApp.Services;
using DesignData.SDS2.Database;
using DesignData.SDS2.HybridPlugins.Communication;
using DesignData.SDS2.HybridPlugins.Services;
using DesignData.SDS2.Model;
using DesignData.SDS2.Setup;
using SDS2.Plugin.UI.Themes;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;
using System.Transactions;
using System.Windows.Input;
using Transaction = DesignData.SDS2.Database.Transaction;

namespace DemoApp.ViewModels
{
    public class MainWindowViewModel : INotifyPropertyChanged
    {
        public SDS2InfoService Sds2InfoService { get; set; }
        private readonly SDS2Connect _sds2Connect;

        private const string AutoStandard = "Auto Standard";
        private const string ShearTab = "Shear Tab";

        public List<string> ConnectionTypes { get; set; } = new List<string>
        {
            AutoStandard,
            ShearTab
        };

        private Member _member;
        public Member Member
        {
            get => _member;
            set
            {
                if (_member == value) { return; }
                _member = value;
                NotifyPropertyChanged();
            }
        }


        private string _profile;
        public string Profile
        {
            get => _profile;
            set
            {
                if (_profile == value) { return; }
                _profile = value;
                NotifyPropertyChanged();
            }
        }


        private string _leftConnection;
        public string LeftConnection
        {
            get => _leftConnection;
            set
            {
                if (_leftConnection == value) { return; }
                _leftConnection = value;
                NotifyPropertyChanged();
            }
        }

        private string _rightConnection;
        public string RightConnection
        {
            get => _rightConnection;
            set
            {
                if (_rightConnection == value) { return; }
                _rightConnection = value;
                NotifyPropertyChanged();
            }
        }

        public MainWindowViewModel(SDS2InfoService sds2InfoService, AppState appState,
            SDS2Connect sds2Connect)
        {
            Sds2InfoService = sds2InfoService;
            _sds2Connect = sds2Connect;
            ThemeSwitcher.SwitchTheme(appState.Theme);
        }

        public ICommand OkCommand { get => new RelayCommand(Ok); }
        public ICommand PickMemberCmd { get => new RelayCommand(PickMember); }
        public ICommand PickProfileCmd { get => new RelayCommand(PickProfile); }



        private void Ok()
        {
            using Transaction transaction = new Transaction(Sds2InfoService.Job, new ImmediateLockHandler());

            List<ConnectionComponent> connections = Member.GetComponents()
                .Select(x => x as ConnectionComponent).ToList();

            transaction.Add(Member);
            transaction.Add(connections[0]);
            transaction.Add(connections[1]);

            transaction.Lock();

            MaterialFile matFile = MaterialFile.Get();

            Member.Shape = matFile.Find(Profile);

            connections[0].InputSpecification = GetConnection(LeftConnection);
            connections[1].InputSpecification = GetConnection(RightConnection);

            transaction.Commit(true);

            transaction.Dispose();


            Environment.Exit(0);
        }

        private ConnectionSpecification GetConnection(string connection)
        {
            return connection switch
            {
                AutoStandard => new AutoStandardSpecification(),
                ShearTab => new ShearTabSpecification(),
                _ => throw new NotImplementedException()
            };
        }

        private void PickMember()
        {
            List<MemberBrief> members = _sds2Connect.MultiMemberLocate();
            Member = Member.Get(members[0].Handle);
        }

        private void PickProfile()
        {
            Profile = _sds2Connect.SelectProfile(
                "Select Profile",
                new List<DesignData.SDS2.HybridPlugins.Models.MaterialType>
                {
                    DesignData.SDS2.HybridPlugins.Models.MaterialType.All
                }
                );
        }


        public event PropertyChangedEventHandler? PropertyChanged;
        private void NotifyPropertyChanged([CallerMemberName] string propertyName = "")
            => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));

    }
}
